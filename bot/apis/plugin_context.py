from typing import Awaitable, Callable
from bot.plugin.manager.plugin_manager import PluginManager
from bot.config.config_manager import ConfigManager
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender


class PluginContext:
    """插件上下文"""

    def __init__(
        self,
        config_manager: ConfigManager,
        plugin_manager: PluginManager,
        reload_plugins: Callable[[], Awaitable[None]],
    ) -> None:
        # 如果在这里构造的时候就初始化， 就不用处理类型警示了
        self.message_sender = sender
        self.config_manager: ConfigManager = config_manager
        self.plugin_manager: PluginManager = plugin_manager
        self.reload_plugins = reload_plugins
        self.reply_creator: Callable = create_reply
        self.sender = sender
