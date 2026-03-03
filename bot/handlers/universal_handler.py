import logging
import datetime
from bot.handlers import CommandHandler
from bot.handlers import ChatHandler
from database.last_message.last_massage_db import LastMessageDatabase
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
        self.last_message_db = LastMessageDatabase()

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

        self.last_message_db.initialize_table()
        self.last_message_db.update_last_message_record(
            event["user_id"],
            datetime.datetime.fromtimestamp(event["time"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )
        if is_command(event):
            await self.command_handler.handle(event)
        else:
            await self.chat_handler.handle(event)
