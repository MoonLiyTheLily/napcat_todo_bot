import logging
from bot.logics import create_mirror_reply


class ChatHandler:
    """
    处理聊天类消息
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def handle(self, event: dict):
        """
        处理聊天类消息
        """
        self.logger.info("ChatHandler已执行")
        return create_mirror_reply(event, True)
