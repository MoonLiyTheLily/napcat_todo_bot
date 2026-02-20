import logging
import asyncio
import datetime
from pathlib import Path
import websockets
from database import LastMessageDatabase
from bot.apis.create_reply import create_reply
from bot.config.config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


async def gravity(websocket):
    """
    重力文案逻辑
    """

    last_message_db = LastMessageDatabase()
    try:
        check_interval = DEFAULT_CONFIG["active"]["gravity"]["check_interval"]
        threshold = DEFAULT_CONFIG["active"]["gravity"]["threshold"]
        while True:
            try:
                # 获取所有用户的最后消息记录
                # 如果距离上次消息超过一定时长，发送重力文案
                # 为了测试可以改成1分钟，默认是60分钟
                user_ids = last_message_db.check_all_user(threshold)
                # user_ids = last_message_db.check_all_user(threshold=1)
                if user_ids is not None:
                    for user_id in user_ids:
                        await gravity_sender(websocket, user_id, last_message_db)
                await asyncio.sleep(check_interval)  # 默认每60分钟检查一次
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


async def gravity_sender(websocket, user_id: str, last_message_db: LastMessageDatabase):
    """
    发送重力文案的函数

    :param user_id: 用户ID
    :param websocket: WebSocket连接
    """
    try:
        logger.info("准备发送重力文案给用户 %s", user_id)
        path = Path(__file__).parent / "gravity.txt"
        gravity_file = open(path, "r", encoding="utf-8")
        for line in gravity_file:
            if not line:
                break
            check_result = last_message_db.check_last_message_record(user_id)
            assert check_result is not None
            last_message_time = check_result.send_time
            current_time = datetime.datetime.now()
            time_diff = current_time - datetime.datetime.strptime(
                last_message_time, "%Y-%m-%d %H:%M:%S"
            )
            if time_diff.total_seconds() < 60:
                logger.info("用户 %s 在发送重力文案时有消息记录，中止发送", user_id)
                return
            # 此处默认移除换行符，因为是一行一行的发
            reply = create_reply().to(user_id).text(line.strip("\n")).build()
            reply_length = len(line.strip())
            sleep_time = max(2, reply_length / 10)
            await asyncio.sleep(sleep_time)
            # 模拟打字的时间，以岛村之刃按照！、？、。的分划，一行最多需要11秒
            await websocket.send(reply)
            logger.info(
                "已发送重力文案给用户 %s: %s", user_id, line.strip()[0:10] + "..."
            )
        logger.info("已完成发送重力文案给用户 %s的任务", user_id)
    except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
        logger.error("WebSocket连接已关闭，无法发送重力文案")
    except Exception as e:
        logger.exception("发送重力文案时出现错误: %s", str(e))
    finally:
        if gravity_file:
            gravity_file.close()
