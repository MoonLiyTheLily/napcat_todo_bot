import logging
import json
from bot.types.command_event import CommandEvent

logger = logging.getLogger(__name__)


class HelpHandler:
    async def handle(self, command_event: CommandEvent):
        """
        显示帮助信息的函数

        :param user_id: 用户id
        :type user_id: str
        :param command_event: 解析获得的参数
        :type command_event: CommandEvent
        """
        logger.info("help_handler已执行")
        help_message = (
            "可用命令列表：\n"
            "/todo - 管理待办事项\n（使用 /todo help 获取更多信息）\n"
            "/help - 显示此帮助信息"
        )
        reply = {
            "action": "send_private_msg",
            "params": {
                "user_id": command_event.user_id,
                "message": {
                    "type": "text",
                    "data": {"text": help_message},
                },
            },
        }
        return json.dumps(reply, ensure_ascii=False)
