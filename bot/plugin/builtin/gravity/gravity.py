import logging
import asyncio
import datetime
from pathlib import Path
from database import LastMessageDatabase
from bot.apis.send_message import sender
from bot.apis.create_reply import create_reply
from bot.apis.registries import register_active
from bot.config.config import config
from bot.plugin.basic_plugin import BasicPlugin

logger = logging.getLogger(__name__)


class ActiveGravity(BasicPlugin):
    def __init__(self) -> None:
        self.last_message_db = LastMessageDatabase()

    @register_active("gravity", 60 * config.get("active.gravity.check_interval"))
    async def gravity(self) -> None:
        """重力文案逻辑"""

        threshold = config.get("active.gravity.threshold")
        try:
            last_message_db = self.last_message_db
            # 获取所有用户的最后消息记录
            # 如果距离上次消息超过一定时长，发送重力文案
            user_ids = await last_message_db.check_all(threshold)
            tasks: list[asyncio.Task] = []
            if user_ids is not None and len(user_ids) > 0:
                for user_id in user_ids:
                    tasks.append(
                        asyncio.create_task(
                            self.gravity_sender(user_id), name=f"{user_id}"
                        )
                    )
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                for task in tasks:
                    if task.exception() is not None:
                        logger.exception(
                            "向用户 %s 的重力消息发生错误: %s",
                            task.get_name(),
                            task.exception(),
                        )

        except asyncio.CancelledError:
            logger.info("重力文案通知任务已取消")
            raise
        except Exception as e:
            logger.exception("重力文案通知出现错误: %s", str(e))
            raise

    async def check_if_need_gravity(self, user_id: int) -> bool:
        last_message_db = self.last_message_db
        check_result = await last_message_db.check(user_id)
        if check_result is None:
            logger.info("用户 %s 没有消息记录，跳过重力检查", user_id)
            return False
        last_message_time = check_result.send_time
        current_time = datetime.datetime.now()
        time_diff = current_time - last_message_time
        if time_diff.total_seconds() < 60:
            logger.info("用户 %s 在发送重力文案时有消息记录，中止发送", user_id)
            return False
        logger.info("用户没有发送消息，上次%s", last_message_time)
        return True

    async def gravity_sender(self, user_id: int) -> None:
        """发送重力文案的函数"""

        logger.info("准备发送重力文案给用户 %s", user_id)
        path = Path(__file__).parent / "gravity.txt"
        with open(path, "r", encoding="utf-8") as gravity_file:
            for line in gravity_file:
                if not line:
                    break
                # 此处默认移除换行符，因为是一行一行的发
                reply = create_reply().to(user_id).text(line.strip("\n")).build()
                reply_length = len(line.strip())
                # 模拟打字的时间，以岛村之刃按照！、？、。的分划，一行最多需要11秒
                sleep_time = max(2, reply_length / 10)
                await asyncio.sleep(sleep_time)
                # sleep后再判定有没有新消息，避免sleep期间用户发消息
                need_to_send = await self.check_if_need_gravity(user_id)
                if need_to_send:
                    await sender.send(reply)
                    logger.info(
                        "已发送重力文案给用户 %s: %s",
                        user_id,
                        line.strip()[0:10] + "...",
                    )
                else:
                    return
            logger.info("已完成发送重力文案给用户 %s的任务", user_id)
