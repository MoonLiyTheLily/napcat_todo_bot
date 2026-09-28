import logging
import asyncio
import websockets

logger = logging.getLogger(__name__)


class MessageSender:
    """信息发送器"""

    def __init__(self):
        self.websocket: websockets.ServerConnection | None = None

    def bind(self, websocket: websockets.ServerConnection) -> None:
        self.websocket = websocket

    def unbind(self, websocket: websockets.ServerConnection) -> None:
        if self.websocket is websocket:
            self.websocket = None

    async def send(self, message) -> bool:
        websocket = self.websocket
        if websocket is None:
            raise ConnectionError("没有可用的 WebSocket 连接")
        try:
            await websocket.send(message=message)
            return True
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
