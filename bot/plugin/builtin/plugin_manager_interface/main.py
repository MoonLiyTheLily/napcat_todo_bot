import logging
from bot.types import CommandEvent
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command

from bot.plugin.manager.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class PluginManagerInterface(BasicPlugin):

    @register_command("pluginreload")
    async def handle(self, command_event: CommandEvent):
        """插件管理器的聊天软件内界面

        目前这个handler除了重载插件没有别的用处
        """
        logger.info("开始重载插件")
        PluginManager._instances[0].reload()
        logger.info("重载插件完成")
        reply = create_reply().to(command_event.user_id).text("已重载所有插件")
        await sender.send(reply.build())
