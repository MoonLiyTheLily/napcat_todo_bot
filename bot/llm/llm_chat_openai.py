import logging
import json
from datetime import datetime
from typing import Any, Sequence
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.config.config import config
from bot.llm.llm_tool_registry import (
    llm_tool_registry,
    LLMToolContext,
    LLMToolRegistryData,
)

logger = logging.getLogger(__name__)


class LLMChatClientOpenAI:
    """管理单个OpenAI Client"""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._cached_api_key: str | None = None
        self._cached_base_url: str | None = None

    @property
    def client(self) -> AsyncOpenAI:
        api_key = config.get("llm.basic.api_key")
        base_url = config.get("llm.basic.base_url")
        if (
            self._client is None
            or self._cached_api_key != api_key
            or self._cached_base_url != base_url
        ):
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self._cached_api_key = api_key
            self._cached_base_url = base_url
        return self._client

    async def chat_completions(
        self, model: str, messages: Sequence[ChatCompletionMessageParam], **kwargs
    ) -> ChatCompletion:
        """对话，对chat.completions.create的一个封装"""
        return await self.client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )


class LLMChatSessionOpenAI:
    """管理单个对话session (带历史记录)"""

    def __init__(self, client: LLMChatClientOpenAI, user_id: int = 1479548851) -> None:
        self.user: int = user_id
        self.client: LLMChatClientOpenAI = client
        self.messages_list: list[ChatCompletionMessageParam] = []
        self.tool_context: LLMToolContext = LLMToolContext(self.user)

    @property
    def target_model(self) -> str:
        return config.get("llm.basic.target_model")

    async def chat(
        self, message: str, tool_list: dict[str, LLMToolRegistryData] | None = None
    ) -> str | None:
        """发送消息"""
        if len(self.messages_list) == 0:
            self.messages_list.append(
                {
                    "role": "system",
                    "content": "最新消息发送时间" + self.tool_context.user_send_time,
                }
            )
        self.messages_list[0]["content"] = (
            "最新消息发送时间" + self.tool_context.user_send_time
        )
        self.messages_list.append({"role": "user", "content": message})
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
                while response.choices[0].message.tool_calls:
                    # 把含 tool_calls 的 assistant 消息加入历史
                    tool_calls_data = []
                    for tc in response.choices[0].message.tool_calls:
                        tool_calls_data.append(
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )
                    self.messages_list.append(
                        {
                            "role": "assistant",
                            "content": response.choices[0].message.content,
                            "tool_calls": tool_calls_data,
                        }
                    )
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
                    tool_result = await tool_data.function(self.tool_context, arguments)
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
        # 依据Deepseek v4 Pro
        # response.choices[0].message.content 可能是 None。有些模型（Qwen）在 tool_calls 以外的场景也会返回 null
        # content。走到 chat() 返回 None → text(None) → JSON 里变成 "text": null → NapCat 显示为空。
        # 这很可能就是你看到"开头两个换行"的原因——不是真的换行，而是 content 为 null 被当空消息显示了。
        self.messages_list.append(
            {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content or "",
            }
        )
        content = response.choices[0].message.content
        if content:
            content = content.lstrip("\n")
        return content

    def clear(self) -> None:
        """重置会话"""
        self.messages_list = [m for m in self.messages_list if m["role"] == "system"]


class LLMChatHandlerOpenAI:
    def __init__(self) -> None:
        self.client: LLMChatClientOpenAI = LLMChatClientOpenAI()
        self.tools: dict[str, LLMToolRegistryData] = llm_tool_registry
        self.sessions: dict[int, LLMChatSessionOpenAI] = {}

    async def handle(self, event: dict[str, Any]) -> None:
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
            reply = create_reply().to(user_id).text("请求回复时出现错误。")
            await sender.send(reply.build())
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
