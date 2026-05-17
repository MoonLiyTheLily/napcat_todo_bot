from typing import Callable
from bot.plugin.manager.plugin_manager import PluginManager
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender


class PluginContext:
    """插件上下文"""

    def __init__(self) -> None:
        self.message_sender = sender
        self.plugin_manager: PluginManager | None = None
        self.reply_creator: Callable = create_reply
        self.sender = sender
