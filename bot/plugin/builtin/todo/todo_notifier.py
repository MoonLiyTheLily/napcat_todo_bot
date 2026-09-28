import logging
from collections import defaultdict
from datetime import datetime
import websockets

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

    async def initialize(self) -> None:
        await self.todo_db.initialize()

    async def shutdown(self) -> None:
        await self.todo_db.close()

    async def _send(self, user_id: int, items: list[Todo], heading: str) -> bool:
        message = heading + "\n" + "\n".join(item.get_list_string() for item in items)
        reply = create_reply().to(user_id).text(message).build()
        return await sender.send(reply)

    @register_active("todo_notifier", config.get("active.todo.notify_interval"))
    async def todo_notify(self):
        """按既有配置周期，汇总发送用户所有未完成待办。"""
        users: dict[int, list[Todo]] = defaultdict(list)
        for item in await self.todo_db.get_unfinished_todos():
            users[item.user_id].append(item)
        for user_id, items in users.items():
            try:
                if await self._send(user_id, items, "您有以下待办事项未完成："):
                    logger.info("已发送待办事项汇总给用户 %s", user_id)
            except (websockets.ConnectionClosed, websockets.InvalidState, ConnectionError):
                raise
            except Exception:
                logger.exception("向用户 %s 发送待办事项汇总失败", user_id)

    @register_active("todo_due_reminder", 30)
    async def remind_due_todos(self):
        """按 notify_time 单次提醒；失败项留待下一轮重试。"""
        users: dict[int, list[Todo]] = defaultdict(list)
        for item in await self.todo_db.get_due_reminders(datetime.now()):
            users[item.user_id].append(item)
        for user_id, items in users.items():
            try:
                sent = await self._send(user_id, items, "您的以下待办已到提醒时间：")
            except (websockets.ConnectionClosed, websockets.InvalidState, ConnectionError):
                raise
            except Exception:
                logger.exception("向用户 %s 发送到期提醒失败，稍后重试", user_id)
                continue
            if sent:
                await self.todo_db.mark_reminders_sent(
                    [item.todo_id for item in items if item.todo_id is not None],
                    datetime.now(),
                )
                logger.info("已发送 %d 项到期提醒给用户 %s", len(items), user_id)
