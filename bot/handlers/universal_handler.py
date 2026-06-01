import logging
import datetime
from bot.handlers import CommandHandler
from bot.handlers import ChatHandler
from bot.handlers.command.command_resolver import is_command
from database.last_message.last_massage_db import LastMessageDatabase
from bot.types import LastMessageRecord
from bot.apis.plugin_context import PluginContext

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
    """处理所有消息的总类"""

    def __init__(self, plugin_context: PluginContext) -> None:
        self.plugin_context = plugin_context
        self.command_handler = CommandHandler(plugin_context)
        self.chat_handler = ChatHandler(plugin_context)
        self.last_message_db = LastMessageDatabase()

    async def handle(self, event: dict):
        """总的消息处理器"""
        if not is_private_chat(event):
            logger.debug("非私聊消息，忽略处理")
            return None
        if not self.last_message_db.inited:
            await self.last_message_db.initialize()
        try:
            new_record = LastMessageRecord(
                user_id=event["user_id"],
                send_time=datetime.datetime.fromtimestamp(event["time"]),
            )
            await self.last_message_db.update(new_record)
            logger.info("已更新用户 %d 的最近消息", event["user_id"])
        except Exception as e:
            logger.warning("更新用户最近消息记录失败: %s", e)
        if is_command(event):
            await self.command_handler.handle(event)
        else:
            await self.chat_handler.handle(event)
