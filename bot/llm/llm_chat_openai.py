import logging
from typing import Sequence
from openai import AsyncOpenAI, RateLimitError, APIError
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.config.config import DEFAULT_CONFIG

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
        try:
            return await self.client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )
        except RateLimitError:
            logger.error("达到用量限制")
            raise
        except APIError as e:
            logger.error("API异常%s", e)
            raise


class LLMChatSessionOpenAI:
    """管理单个对话session (带历史记录)"""

    def __init__(self, client, user_id="1479548851"):
        self.user = user_id
        self.client: LLMChatClientOpenAI = client
        self.target_model = target_model
        self.messages_list = []

    async def chat(self, message: str):
        """发送消息"""
        self.messages_list.append({"role": "user", "content": message})
        try:
            assert self.target_model is not None, "目标模型不能为空"
            response = await self.client.chat_completions(
                model=self.target_model,
                messages=self.messages_list,
            )
        except Exception as e:
            self.messages_list.pop()
            logger.exception("获取LLM回复消息失败%s", e)
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

        raw_reply = await target_session.chat(user_message)
        reply = create_reply().to(user_id).text(raw_reply)
        await sender.send(reply.build())
        logger.info("LLMChat已经处理完来自: %s 的消息", user_id)


if __name__ == "__main__":
    cli = LLMChatClientOpenAI()
    test = LLMChatSessionOpenAI(cli, "")
    while True:
        usermsg = input()
        if usermsg == "p":
            print(test.messages_list)
            continue
        elif usermsg == "clear":
            test.clear()
        res = test.chat(usermsg)
        print(res)
