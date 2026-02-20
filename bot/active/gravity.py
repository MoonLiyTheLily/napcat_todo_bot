import logging
import asyncio
import websockets
from pathlib import Path
from database import LastMessageDatabase
from bot.apis.create_reply import create_reply

logger = logging.getLogger(__name__)


async def gravity(websocket):
    """
    重力文案逻辑
    """

    last_message_db = LastMessageDatabase()
    try:
        while True:
            try:
                # 获取所有用户的最后消息记录
                # 如果距离上次消息超过一定时长，发送重力文案
                user_ids = last_message_db.check_all_user()
                if user_ids is not None:
                    for user_id in user_ids:
                        await gravity_sender(websocket, user_id)
                await asyncio.sleep(1200)  # 每20min检查一次
            except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
                logger.error("WebSocket连接已关闭，停止重力文案通知")
                return
            except asyncio.CancelledError:
                logger.info("重力文案通知任务已取消")
                raise
            except Exception as e:
                logger.exception("重力文案通知出现错误: %s，将在1分钟后重试", str(e))
                raise
    finally:
        last_message_db.close()


async def gravity_sender(websocket, user_id: str):
    """
    发送重力文案的函数

    :param user_id: 用户ID
    :param websocket: WebSocket连接
    """
    try:
        path = Path(__file__).parent / "gravity.txt"
        gravity_file = open(path, "r", encoding="utf-8")
        for line in gravity_file:
            if not line:
                break
            # 此处默认移除换行符，因为是一行一行的发
            reply = create_reply().to(user_id).text(line.strip("\n")).build()
            await websocket.send(reply)
            await asyncio.sleep(5)
    except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
        logger.error("WebSocket连接已关闭，无法发送重力文案")
    except Exception as e:
        logger.exception("发送重力文案时出现错误: %s", str(e))
    finally:
        if gravity_file:
            gravity_file.close()
