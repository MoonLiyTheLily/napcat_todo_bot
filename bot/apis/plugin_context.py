# 目前未使用

from typing import Callable
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender


# 目前未使用
class PluginContext:
    """插件上下文"""

    def __init__(self) -> None:
        self.message_sender = sender
        self.reply_creator: Callable = create_reply

    async def send(self, message):
        await self.message_sender.send(message)

    def create_reply(self):
        return self.reply_creator()
