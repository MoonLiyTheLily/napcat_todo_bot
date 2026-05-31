import logging
import asyncio
import websockets
from typing import List
from bot.plugin.basic_plugin import BasicPlugin
from bot.types import Todo
from database import TodoDatabase
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.apis.registries import register_active
from bot.config.config import config

logger = logging.getLogger(__name__)


class TodoNotifier(BasicPlugin):
    def __init__(self) -> None:
        self.todo_db = TodoDatabase()

    async def todo_sender(self, user_id, todo_items: List[Todo]):
        user_todos = []
        for item in todo_items:
            if not item.is_done:
                user_todos.append(item.get_list_string())
        if len(user_todos) > 0:
            message = "您有以下待办事项未完成：\n" + "\n".join(user_todos)
            reply = create_reply().to(user_id).text(message).build()
            await sender.send(reply)
            logger.info("已发送待办事项通知给用户%s", user_id)

    @register_active("todo_notifier", 60 * config.get("active.todo.notify_interval"))
    async def todo_notify(self):
        """Todo定时通知函数"""
        try:
            logger.info("检查待办事项通知")
            users = await self.todo_db.get_users()
            if users is not None and len(users) > 0:
                tasks: list[asyncio.Task] = []
                for user_id in users:
                    todo_items = await self.todo_db.get_todos(user_id)
                    tasks.append(
                        asyncio.create_task(
                            self.todo_sender(user_id, todo_items), name=f"{user_id}"
                        )
                    )
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                for task in tasks:
                    if task.exception() is not None:
                        logger.exception(
                            "向用户 %s 的待办通知发生错误: %s",
                            task.get_name(),
                            task.exception(),
                        )
        except websockets.ConnectionClosedError, websockets.ConnectionClosed:
            logger.error("WebSocket连接已关闭，停止待办事项通知")
            return
        except asyncio.CancelledError:
            logger.info("待办事项通知任务已取消")
            raise
        except Exception as e:
            logger.exception("待办事项通知出现错误: %s", str(e))
            raise
