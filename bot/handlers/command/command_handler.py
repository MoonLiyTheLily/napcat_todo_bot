import logging
import bot.command
from bot.handlers.command.command_resolver import command_resolver
from bot.types import CommandEvent

logger = logging.getLogger(__name__)


class CommandHandler:
    """命令处理类"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.commands = {
            "todo": bot.command.TodoHandler().handle,
            "help": bot.command.HelpHandler().handle,
            "not_found": bot.command.NotFoundHandler().handle,
            "config": bot.command.ConfigManagerHandler().handle,
        }
        # 命令需要在command里导出其handler，再在此处注册

    async def handle(self, event: dict):
        await self.handle_command_event(command_resolver(event))

    async def handle_command_event(self, command_event: CommandEvent):
        """处理所有的命令

        :param self: 说明
        :param user_id: 说明
        :type user_id: int
        :param command_event: 说明
        :type command_event: CommandEvent
        """
        logger.debug("CommandHandler已执行")
        handler = self.commands.get(command_event.command, self.commands["not_found"])
        await handler(command_event)
