import logging
from bot.llm.llm_chat_openai import LLMChatHandlerOpenAI
from bot.logics import create_mirror_reply
from bot.config.config import DEFAULT_CONFIG


class ChatHandler:
    """
    处理聊天类消息
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.llm_handler = LLMChatHandlerOpenAI()

    async def handle(self, event: dict):
        """
        处理聊天类消息
        """
        self.logger.debug("ChatHandler已执行")
        enable_llm_reply = DEFAULT_CONFIG["llm"]["enabled"]
        if enable_llm_reply:
            await self.llm_handler.handle(event)
            return
        await create_mirror_reply(event, True)
