import logging
from bot.types import CommandEvent
from bot.apis.plugin_context import PluginContext
from bot.apis.create_reply import create_reply
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command

logger = logging.getLogger(__name__)


class NotFoundHandler(BasicPlugin):

    @register_command("not_found")
    async def handle(self, context: PluginContext, command_event: CommandEvent):
        """没找到目标命令时调用的函数

        :param context: 插件上下文
        :type context: PluginContext
        :param command_event: 解析获得的参数
        :type command_event: CommandEvent
        """
        logger.info(command_event.command)
        logger.info("not_found_handler已执行")
        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("未找到命令。/help 可以查看目前支持的命令列表。")
        )
        await context.sender.send(reply.build())


PLUGIN_CLASSES = (NotFoundHandler,)
