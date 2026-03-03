import sqlite3
import logging
import datetime
from pathlib import Path
from bot.types import LastMessageRecordItem

logger = logging.getLogger(__name__)


class LastMessageDatabase:
    """LastMessage数据库类，包含了对last_message表的基本操作"""

    def __init__(self) -> None:
        db_path = Path(__file__).parent.parent / "test.db"
        self.db = sqlite3.connect(str(db_path))
        self.last_result = None

    def __del__(self):
        self.db.close()

    def is_initialized(self):
        """检查数据库是否初始化（也就是建立了last_message表）

        :param self: 说明
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='last_message'"
        )
        return cursor.fetchone() is not None

    def create_last_message_table(self):
        """建立表。如果没有初始化，就使用这个函数建表

        :param self: 说明
        """
        cursor = self.db.cursor()
        # user_id设置为唯一，方便后续的插入/更新操作（如果user_id已经存在，就更新send_time）
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS last_message (\
                id INTEGER PRIMARY KEY,\
                user_id VARCHAR(15) NOT NULL UNIQUE,\
                send_time VARCHAR(30) DEFAULT CURRENT_TIMESTAMP)"
        )
        self.db.commit()

    def initialize_table(self):
        """初始化函数

        :param self: 说明
        """
        if not self.is_initialized():
            self.create_last_message_table()
            self.db.commit()

    def sql_result_to_last_message_record_items(
        self, sql_result
    ) -> list[LastMessageRecordItem]:
        """将从数据库中获得的结果转换为LastMessageRecordItems的list

        :param self: 说明
        :param sql_result: 从数据库中获得的结果
        """
        return [
            LastMessageRecordItem(
                user_id=row[0],
                send_time=row[1],
            )
            for row in sql_result
        ]

    def check_last_message_record(self, user_id: str):
        """根据user_id获取最后消息记录

        :param self: 说明
        :param user_id: 用户id
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT user_id, send_time FROM last_message WHERE user_id = ?", (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return LastMessageRecordItem(user_id=result[0], send_time=result[1])
        else:
            return None

    def add_last_message_record(self, user_id: str, send_time: str):
        """添加最后消息记录

        :param self: 说明
        :param user_id: 用户id
        :param send_time: 发送时间
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO last_message (user_id, send_time) VALUES (?, ?)",
            (user_id, send_time),
        )
        self.db.commit()

    def update_last_message_record(self, user_id: str, send_time: str):
        """更新最后消息记录，如果没有就插入

        另外由于这个函数在main里也有调用，所以同时也处理删除过于老旧的记录

        :param self: 说明
        :param user_id: 用户id
        :param send_time: 发送时间
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO last_message (user_id, send_time) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET send_time=excluded.send_time",
            (user_id, send_time),
        )
        cursor.execute(
            "SELECT id FROM last_message WHERE send_time < ?",
            (datetime.datetime.now() - datetime.timedelta(days=1),),
        )
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                self.delete_last_message_record(row[0])
                logger.info("已删除过于老旧的消息记录，来自用户: %s", row[1])
        self.db.commit()
        logger.info("已更新用户 %s 的最后一次信息，发送时间: %s", user_id, send_time)

    def delete_last_message_record(self, user_id: str):
        """根据user_id删除最后消息记录

        :param self: 说明
        :param user_id: 用户id
        """
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM last_message WHERE user_id = ?", (user_id,))
        self.db.commit()

    def check_all_user(
        self, threshold: int = 60, earliest: int = 1440
    ) -> list[str] | None:
        """返回所有有最近消息记录的用户id列表

        默认参数是过去1天内发送过消息，但是过去1小时内没有

        :param threshold: 多少分钟内发送过消息，默认60分钟
        :param earliest: 最早多少分钟之前发送过消息，默认为1天
        """
        if not self.is_initialized():
            return None
        elif threshold < 0 or earliest < 0:
            logger.warning("参数threshold和earliest必须为非负整数")
            return None
        elif threshold >= earliest:
            logger.warning("参数threshold必须小于earliest")
            return None
        else:
            logger.info("所有%d到%d分钟前发送过消息的用户id", earliest, threshold)

            latest_time = datetime.datetime.now() - datetime.timedelta(
                minutes=threshold
            )
            earliest_time = datetime.datetime.now() - datetime.timedelta(
                minutes=earliest
            )

            cursor = self.db.cursor()
            cursor.execute(
                "SELECT DISTINCT user_id FROM last_message WHERE send_time BETWEEN ? AND ?",
                (earliest_time, latest_time),
            )
            data = cursor.fetchall()
            user_ids = [item[0] for item in data]
            logger.info("获得的用户id列表: %s", user_ids)
            return user_ids

    def close(self):
        """关闭数据库连接

        :param self: 说明
        """
        self.db.close()
