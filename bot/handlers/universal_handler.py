import logging
from bot.handlers import CommandHandler
from bot.handlers import ChatHandler
from bot.handlers.command.command_resolver import is_command

logger = logging.getLogger(__name__)


def is_private_chat(event: dict) -> bool:
    """
    判断当前消息事件是不是私聊，返回bool

    :param event: 已经转化成dict的NapCatQQ事件列表
    :type event: dict
    """
    return (
        event.get("post_type") == "message" and event.get("message_type") == "private"
    )


class UniversalHandler:
    """
    处理所有消息的总类
    """

    def __init__(self) -> None:
        self.command_handler = CommandHandler()
        self.chat_handler = ChatHandler()

    async def handle(self, event: dict):
        """
        总的消息处理器

        :param self: 说明
        :param event: 说明
        :type event: dict
        """
        if not is_private_chat(event):
            logger.info("非私聊消息，忽略处理")
            return None
        if is_command(event):
            return await self.command_handler.handle(event)
        else:
            return await self.chat_handler.handle(event)
