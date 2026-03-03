import logging
import asyncio
import websockets

logger = logging.getLogger(__name__)


# 本类未使用
class MessageSender:
    def __init__(self):
        self.websocket: websockets.ServerConnection

    async def send(self, message):
        assert self.websocket is not None
        try:
            await self.websocket.send(message=message)
        except (
            websockets.ConnectionClosedError,
            websockets.ConnectionClosed,
            websockets.InvalidState,
        ):
            logger.error("WebSocket连接关闭，停止发送消息")
            raise
        except asyncio.TimeoutError:
            logger.warning("WebSocket链接超时，停止发送消息")
            return False
        except Exception as e:
            logger.exception("发送消息出现错误: %s", str(e))
            return False


sender = MessageSender()
