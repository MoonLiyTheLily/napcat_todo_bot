import logging
from bot.types import CommandEvent
from bot.apis.create_reply import create_reply
from bot.apis.plugin_context import PluginContext
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command
from bot.config.config import config

logger = logging.getLogger(__name__)


class PluginManagerInterface(BasicPlugin):
    """插件管理器的聊天软件内界面"""

    @register_command("pluginreload")
    async def handle(self, context: PluginContext, command_event: CommandEvent) -> None:
        """重载所有插件"""
        user_id = command_event.user_id
        admin_user_id = config.get("admin_user_id")
        if user_id != admin_user_id:
            reply = create_reply().to(user_id).text("您不是管理员，不能使用此命令")
            await context.sender.send(reply.build())
            return
        logger.info("开始重载插件")
        try:
            await context.reload_plugins()
        except Exception:
            logger.exception("重载插件失败")
            reply = create_reply().to(command_event.user_id).text("重载插件错误")
            await context.sender.send(reply.build())
            return
        logger.info("重载插件完成")
        reply = create_reply().to(command_event.user_id).text("已重载所有插件")
        await context.sender.send(reply.build())


PLUGIN_CLASSES = (PluginManagerInterface,)
