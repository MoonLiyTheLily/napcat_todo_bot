import logging
from bot.types.command_event import CommandEvent
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import register_command

logger = logging.getLogger(__name__)


class HelpHandler(BasicPlugin):
    @register_command("help")
    async def handle(self, command_event: CommandEvent):
        """显示帮助信息的函数

        :param user_id: 用户id
        :type user_id: int
        :param command_event: 解析获得的参数
        :type command_event: CommandEvent
        """
        logger.info("help_handler已执行")
        help_message = (
            "可用命令列表：\n"
            "/todo - 管理待办事项\n（使用 /todo help 获取更多信息）\n"
            "/config - 仅管理员可用，修改配置\n"
            "/pluginreload - 仅管理员可用，重载插件\n"
            "/help - 显示此帮助信息\n"
            "stat - 显示现在Session内的消息量\n"
            "clear - 清除当前Session,，开始新对话"
        )
        reply = create_reply().to(command_event.user_id).text(help_message)
        await sender.send(reply.build())
