import logging
from typing import List
from datetime import datetime, timedelta
from bot.types import LastMessageRecord
from database.basic_database import BasicDatabase
from sqlmodel import select, delete, and_

logger = logging.getLogger(__name__)


class LastMessageDatabase(BasicDatabase):
    def __init__(self) -> None:
        super().__init__()
        self.inited = False

    async def initialize(self) -> None:
        async with self.engine.begin() as s:
            await s.run_sync(LastMessageRecord.metadata.create_all)
            self.inited = True

    async def check(self, user_id: int) -> LastMessageRecord | None:
        """根据user_id获取最后消息记录"""
        async with self.get_session() as s:
            res = await s.get(LastMessageRecord, user_id)
            return res

    async def check_all(self, threshold: int = 60, earliest: int = 1440) -> List[int]:
        if threshold < 0 or earliest < 0:
            logger.warning("参数threshold和earliest必须为非负整数")
            return []
        elif threshold >= earliest:
            logger.warning("参数threshold必须小于earliest")
            return []
        else:
            logger.info("所有%d到%d分钟前发送过消息的用户id", earliest, threshold)
            latest_time = datetime.now() - timedelta(minutes=threshold)
            earliest_time = datetime.now() - timedelta(minutes=earliest)

        stmt = select(LastMessageRecord.user_id).where(
            and_(
                LastMessageRecord.send_time < latest_time,
                LastMessageRecord.send_time > earliest_time,
            )
        )
        async with self.get_session() as s:
            res = await s.execute(stmt)
            res = res.scalars().all()
            return_value = []
            for r in res:
                return_value.append(r)
            logger.info("获得的用户id列表: %s", return_value)
            return return_value

    async def add(self, record: LastMessageRecord) -> None:
        """添加最后消息记录"""
        async with self.get_session() as s:
            s.add(record)
            await s.commit()

    async def update(self, user_id: int, send_time: datetime) -> None:
        """更新最后消息记录，如果没有就插入

        同时负责删除过老的记录
        """

        stmt = select(LastMessageRecord.user_id).where(
            LastMessageRecord.send_time < datetime.now() - timedelta(hours=12)  # type: ignore
        )
        try:
            async with self.get_session() as s:
                record = LastMessageRecord(user_id=user_id, send_time=send_time)
                res = await s.get(LastMessageRecord, record.user_id)
                if res:
                    res.send_time = send_time
                else:
                    await self.add(record)
                    logger.info(
                        "已更新用户 %s 的最后一次信息，发送时间: %s",
                        record.user_id,
                        record.send_time,
                    )
                res = await s.execute(stmt)
                res_sequence = res.scalars().all()
                if len(res_sequence) > 0:
                    del_stmt = delete(LastMessageRecord).where(
                        LastMessageRecord.send_time < datetime.now() - timedelta(hours=12)  # type: ignore
                    )
                    await s.execute(del_stmt)
                    logger.info("已删除过于老旧的消息记录%s", res_sequence)
        except Exception as e:
            logger.exception(e)

    async def delete(self, user_id: int):
        async with self.get_session() as s:
            res = await s.get(LastMessageRecord, user_id)
            if res is not None:
                await s.delete(res)
