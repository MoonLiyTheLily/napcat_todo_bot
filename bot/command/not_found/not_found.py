import logging
from bot.types import CommandEvent
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender

logger = logging.getLogger(__name__)


class NotFoundHandler:

    async def handle(self, command_event: CommandEvent):
        """
        没找到命令的话，调用的函数

        :param user_id: 用户id
        :type user_id: str
        :param parameters: 解析获得的参数
        :type parameters: list
        """
        logger.info(command_event.command)
        logger.info("not_found_handler已执行")
        reply = (
            create_reply()
            .to(command_event.user_id)
            .text("未找到命令。/help 可以查看目前支持的命令列表。")
        )
        await sender.send(reply.build())
