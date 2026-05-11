import logging
from bot.types import CommandEvent
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command
from bot.plugin.manager.plugin_manager import PluginManager
from bot.config.config import config

logger = logging.getLogger(__name__)


class PluginManagerInterface(BasicPlugin):
    """插件管理器的聊天软件内界面"""

    @register_command("pluginreload")
    async def handle(self, command_event: CommandEvent) -> None:
        """重载所有插件"""

        user_id = command_event.user_id
        admin_user_id = config.get("admin_user_id")
        if user_id != admin_user_id:
            reply = create_reply().to(user_id).text("您不是管理员，不能使用此命令。")
            # logger.info("管理员用户id:%s 当前用户id:%s", admin_user_id, user_id)
            # print(type(user_id), "H", type(admin_user_id))
            await sender.send(reply.build())
        logger.info("开始重载插件")
        PluginManager._instances[0].reload()
        logger.info("重载插件完成")
        reply = create_reply().to(command_event.user_id).text("已重载所有插件")
        await sender.send(reply.build())
