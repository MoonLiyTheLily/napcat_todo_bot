import sqlite3
import logging
from pathlib import Path
from bot.types import TodoItem

logger = logging.getLogger(__name__)


class TodoDatabase:
    """Todo数据库类，包含了对todo表的基本操作"""

    def __init__(self) -> None:
        db_path = Path(__file__).parent.parent / "test.db"
        self.db = sqlite3.connect(str(db_path))
        self.last_result = None

    def is_initialized(self):
        """检查数据库是否初始化（也就是建立了todo_table）

        :param self: 说明
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='todo_table'"
        )
        return cursor.fetchone() is not None

    def create_todo_table(self):
        """建立表。如果没有初始化，就使用这个函数建表

        :param self: 说明
        """
        cursor = self.db.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS todo_table (\
                todo_id INTEGER PRIMARY KEY ,\
                user_id VARCHAR(15) NOT NULL,\
                content VARCHAR(255) NOT NULL,\
                is_done BOOLEAN NOT NULL DEFAULT 0,\
                user_created_at VARCHAR(30) DEFAULT CURRENT_TIMESTAMP,\
                updated_at VARCHAR(30) DEFAULT CURRENT_TIMESTAMP,\
                completed_at VARCHAR(30))"
        )
        self.db.commit()

    def initialize_table(self):
        """初始化函数

        :param self: 说明
        """
        if not self.is_initialized():
            self.create_todo_table()

    def sql_result_to_todoitems(self, sql_result) -> list[TodoItem]:
        """将从数据库中获得的结果转换为TodoItem的list

        :param sql_result: 从数据库中获得的结果
        :type sql_result: list
        """
        todo_items = []
        for item in sql_result:
            todo_item = TodoItem(
                database_id=item[0],
                user_id=item[1],
                content=item[2],
                is_done=bool(item[3]),
                user_create_time=item[4],
                update_time=item[5],
                complete_time=item[6],
            )
            todo_items.append(todo_item)
        return todo_items

    def todoitems_to_sql_values(self, todo_items: list[TodoItem]):
        """将TodoItem的list转换为可以插入数据库的值

        :param todo_items: todo items的list
        :type todo_items: list
        """
        sql_values = []
        for item in todo_items:
            values = (
                item.user_id,
                item.content,
                int(item.is_done),
                item.user_create_time,
                item.update_time,
                item.complete_time,
            )
            sql_values.append(values)
        return sql_values

    def check_todo(self, user_id: int):
        """以List形式返回用户的所有todo。如果没有，就是None

        :param self: 说明
        :param user_id: 用户id
        :type user_id: int
        """
        if not self.is_initialized():
            return None
        else:
            logger.info("检查用户%s的待办事项", user_id)
            logger.info("查询语句为SELECT * FROM todo_table WHERE user_id=%s", user_id)

            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM todo_table WHERE user_id=?", (user_id,))
            data = cursor.fetchall()
            logger.debug("获得的待办事项数据: %s", data)
            logger.info("获得的待办事项数: %d", len(data))
            return self.sql_result_to_todoitems(data)

    def check_all_user(self):
        """返回所有有待办事项的用户id列表

        :param self: 说明
        """
        if not self.is_initialized():
            return None
        else:
            logger.info("检查所有有待办事项的用户id")

            cursor = self.db.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM todo_table")
            data = cursor.fetchall()
            user_ids = [item[0] for item in data]
            logger.info("获得的用户id列表: %s", user_ids)
            return user_ids

    def add_todo(self, user_id: int, content: str, user_create_time: str):
        """给定用户和内容，以及发送时间，加入待办表

        :param user_id: 用户id
        :type user_id: int
        :param content: 待办内容
        :type content: str
        :param user_create_time: 用户创建待办的时间，也就是发送时间
        :type user_create_time: str
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO todo_table (user_id,content,user_created_at,updated_at)\
             VALUES (?,?,?,datetime('now', 'localtime'))",
            (user_id, content, user_create_time),
        )
        self.db.commit()

    def add_todo_todoitem(self, todo_item: TodoItem):
        """给定一个TodoItem，加入待办表

        :param self: 说明
        :param todo_item: 说明
        :type todo_item: TodoItem
        """
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO todo_table (user_id,content,is_done,user_created_at,updated_at,completed_at)\
             VALUES (?,?,?,?,?,?)",
            (
                todo_item.user_id,
                todo_item.content,
                int(todo_item.is_done),
                todo_item.user_create_time,
                todo_item.update_time,
                todo_item.complete_time,
            ),
        )
        self.db.commit()

    def modify_todo(self, user_id: int, todo_id: int, new_content: str):
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE todo_table SET content=?, updated_at=datetime('now', 'localtime')\
             WHERE user_id=? AND todo_id=?",
            (new_content, user_id, todo_id),
        )
        self.db.commit()
        return None

    def complete_todo(self, user_id: int, todo_id: int, complete_time: str = ""):
        """设定某个Todo为已完成

        :param user_id: 用户id
        :type user_id: int
        :param todo_id: todo事项在数据库里的唯一id
        :type todo_id: int
        :param complete_time: 完成时间
        :type complete_time: str
        """
        cursor = self.db.cursor()
        if complete_time == "":
            cursor.execute(
                "UPDATE todo_table SET is_done=1, completed_at=datetime('now', 'localtime'), updated_at=datetime('now', 'localtime')\
             WHERE user_id=? AND todo_id=?",
                (user_id, todo_id),
            )
        else:
            cursor.execute(
                "UPDATE todo_table SET is_done=1, completed_at=?, updated_at=datetime('now', 'localtime')\
                 WHERE user_id=? AND todo_id=?",
                (complete_time, user_id, todo_id),
            )
        self.db.commit()
        return None

    def uncomplete_todo(self, user_id: int, todo_id: int):
        """设定某个Todo为未完成

        :param user_id: 用户id
        :type user_id: int
        :param todo_id: todo事项在数据库里的唯一id
        :type todo_id: int
        """
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE todo_table SET is_done=0, completed_at=NULL, updated_at=datetime('now', 'localtime')\
             WHERE user_id=? AND todo_id=?",
            (user_id, todo_id),
        )
        self.db.commit()
        return None

    def delete_todo(self, user_id: int, todo_id: int):
        """删除某个Todo

        :param user_id: 用户id
        :type user_id: int
        :param todo_id: todo事项在数据库里的唯一id
        :type todo_id: int
        """
        cursor = self.db.cursor()
        cursor.execute(
            "DELETE FROM todo_table WHERE user_id=? AND todo_id=?",
            (user_id, todo_id),
        )
        self.db.commit()
        return None

    def close(self):
        self.db.close()
