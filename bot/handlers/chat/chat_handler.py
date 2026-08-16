import logging
from typing import Any
from bot.llm.llm_chat_openai import LLMChatHandlerOpenAI
from bot.apis.mirror_reply import create_mirror_reply
from bot.apis.plugin_context import PluginContext


class ChatHandler:
    """处理聊天类消息"""

    def __init__(self, plugin_context: PluginContext) -> None:
        self.logger = logging.getLogger(__name__)
        self.plugin_context = plugin_context
        self.llm_handler = LLMChatHandlerOpenAI()

    async def handle(self, event: dict[str, Any]) -> None:
        self.logger.debug("ChatHandler已执行")
        enable_llm_reply: bool = self.plugin_context.config_manager.get("llm.enable")
        if enable_llm_reply:
            await self.llm_handler.handle(event)
            return
        await create_mirror_reply(event, True, True)
