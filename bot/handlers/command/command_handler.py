import logging
from bot.handlers.command.command_resolver import command_resolver
from bot.types import CommandEvent
from bot.plugin.manager.plugin_registry import command_registry
from bot.apis.plugin_context import PluginContext

logger = logging.getLogger(__name__)


class CommandHandler:
    """命令处理类"""

    def __init__(self, plugin_context: PluginContext) -> None:
        self.logger = logging.getLogger(__name__)
        self.plugin_context = plugin_context
        self.commands = command_registry
        # 命令需要在command里导出其handler，再在此处注册

    async def handle(self, event: dict):
        await self.handle_command_event(command_resolver(event))

    async def handle_command_event(self, command_event: CommandEvent | None):
        """处理所有的命令

        :param self: 说明
        :param user_id: 说明
        :type user_id: int
        :param command_event: 说明
        :type command_event: CommandEvent
        """
        if command_event is None:
            return
        logger.debug("CommandHandler已执行")
        handler_data = self.commands.get(command_event.command)
        if handler_data is None or handler_data.function is None:
            handler_data = self.commands.get("not_found")
        if handler_data is not None and handler_data.function is not None:
            await handler_data.function(self.plugin_context, command_event)
