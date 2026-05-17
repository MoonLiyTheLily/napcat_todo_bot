from typing import Callable
from bot.plugin.manager.plugin_manager import PluginManager
from bot.config.config_manager import ConfigManager
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender


class PluginContext:
    """插件上下文"""

    def __init__(
        self, config_manager: ConfigManager, plugin_manager: PluginManager
    ) -> None:
        # 如果在这里构造的时候就初始化， 就不用处理乱七八糟的类型警示了
        # 工程实践+1
        self.message_sender = sender
        self.config_manager: ConfigManager = config_manager
        self.plugin_manager: PluginManager = plugin_manager
        self.reply_creator: Callable = create_reply
        self.sender = sender
