import logging
import json
from datetime import datetime
from typing import Sequence
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.config.config import DEFAULT_CONFIG
from bot.llm.llm_tool_registry import (
    llm_tool_registry,
    LLMToolContext,
    LLMToolRegistryData,
)

api_key = DEFAULT_CONFIG["llm"]["basic"]["api_key"]
base_url = DEFAULT_CONFIG["llm"]["basic"]["base_url"]
target_model = DEFAULT_CONFIG["llm"]["basic"]["target_model"]

logger = logging.getLogger(__name__)


class LLMChatClientOpenAI:
    """管理单个OpenAI Client"""

    def __init__(self) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.client: AsyncOpenAI = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def chat_completions(
        self, model: str, messages: Sequence[ChatCompletionMessageParam], **kwargs
    ) -> ChatCompletion:
        """对话，对chat.completions.create的一个封装"""
        return await self.client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )


class LLMChatSessionOpenAI:
    """管理单个对话session (带历史记录)"""

    def __init__(self, client, user_id=1479548851):
        self.user = user_id
        self.client: LLMChatClientOpenAI = client
        self.target_model = target_model
        self.messages_list = []
        self.tool_context = LLMToolContext(self.user)

    async def chat(
        self, message: str, tool_list: dict[str, LLMToolRegistryData] | None = None
    ):
        """发送消息"""
        self.messages_list.append({"role": "user", "content": message})
        self.messages_list.append(
            {
                "role": "system",
                "content": "本条消息发送时间" + self.tool_context.user_send_time,
            }
        )
        try:
            assert self.target_model is not None, "目标模型不能为空"
            if tool_list is not None:
                tool_descriptions = []
                for _, tool_data in tool_list.items():
                    tool_descriptions.append(tool_data.description)
                response = await self.client.chat_completions(
                    model=self.target_model,
                    messages=self.messages_list,
                    tools=tool_descriptions,
                )
                while response.choices[0].message.tool_calls is not None:
                    # Qwen疑似会返回两个id不一样但是内容几乎一样的函数调用
                    # 阿里云文档也只取了第一个tool_call，这里决定学习
                    tool_call = response.choices[0].message.tool_calls[0]
                    # VS Code的Pylance有可能提示function不存在，大概是不需要管
                    function_name = tool_call.function.name  # type: ignore
                    arguments = json.loads(tool_call.function.arguments)  # type: ignore
                    logger.info("正在调用工具 [%s]，参数：%s", function_name, arguments)
                    # 执行工具
                    tool_data = tool_list.get(function_name, tool_list["not_found"])
                    assert (
                        tool_data.function is not None
                    ), f"调用的LLMTool {tool_data.name} 函数字段为None"
                    tool_result = tool_data.function(self.tool_context, arguments)
                    # 构造工具返回信息
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                    logger.info("工具返回：%s", tool_message["content"])
                    self.messages_list.append(tool_message)
                    # 再次调用模型，获取总结后的自然语言回复
                    response = await self.client.chat_completions(
                        model=self.target_model,
                        messages=self.messages_list,
                        tools=tool_descriptions,
                    )
                    assistant_output = response.choices[0].message
                    if assistant_output.content is None:
                        assistant_output.content = ""
                    self.messages_list.append(
                        {"role": "assistant", "content": assistant_output.content}
                    )
            else:
                response = await self.client.chat_completions(
                    model=self.target_model,
                    messages=self.messages_list,
                )
        except Exception:
            # 回滚到上一条用户消息
            while self.messages_list[-1]["role"] != "user":
                self.messages_list.pop()
            raise
        self.messages_list.append(
            {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content,
            }
        )
        return response.choices[0].message.content

    def clear(self):
        """重置会话"""
        self.messages_list = [m for m in self.messages_list if m["role"] == "system"]


class LLMChatHandlerOpenAI:
    def __init__(self) -> None:
        self.client: LLMChatClientOpenAI = LLMChatClientOpenAI()
        self.tools: dict[str, LLMToolRegistryData] = llm_tool_registry
        self.sessions = {}

    async def handle(self, event: dict):
        user_id = event["user_id"]
        logger.info("LLMChat正在处理来自: %s 的消息", user_id)
        user_message = ""
        # 目前只支持合并成单句的消息
        for msg in event["message"]:
            if msg["type"] == "text":
                user_message += msg["data"]["text"]

        target_session = self.sessions.get(user_id)
        if target_session is None:
            self.sessions[user_id] = LLMChatSessionOpenAI(self.client, user_id)
            target_session = self.sessions[user_id]
        assert isinstance(target_session, LLMChatSessionOpenAI)

        target_session.tool_context.user_send_time = datetime.fromtimestamp(
            event["time"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        if user_message == "":
            logger.info("当前用户(%s)没有发送文本消息或者获取的文本消息为空", user_id)
            await sender.send(
                create_reply()
                .to(user_id)
                .text("发送的消息似乎不含有文本，无法处理。")
                .build()
            )
            return
        # 处理一些基本的命令
        if user_message == "stat":
            await sender.send(
                create_reply()
                .to(user_id)
                .text(f"现在的Session内有{len(target_session.messages_list)}条消息。")
                .build()
            )
            logger.info("LLMChat已响应来自 %s 的命令 %s", user_id, user_message)
            return
        # 如果是清除Session就延后一下在这里查找完顺便执行
        if user_message == "clear":
            target_session.clear()
            await sender.send(
                create_reply().to(user_id).text("已经清除当前Session的消息记录").build()
            )
            logger.info("LLMChat已响应来自 %s 的命令 %s", user_id, user_message)
            return

        try:
            raw_reply = await target_session.chat(user_message, self.tools)
            reply = create_reply().to(user_id).text(raw_reply)
            await sender.send(reply.build())
        except Exception as e:
            logger.exception("请求回复时出现错误%s", e)
        logger.info("LLMChat已经处理完来自: %s 的消息", user_id)


if __name__ == "__main__":
    cli = LLMChatClientOpenAI()
    test = LLMChatSessionOpenAI(cli)
    while True:
        usermsg = input()
        if usermsg == "p":
            print(test.messages_list)
            continue
        elif usermsg == "clear":
            test.clear()
        res = test.chat(usermsg)
        print(res)
