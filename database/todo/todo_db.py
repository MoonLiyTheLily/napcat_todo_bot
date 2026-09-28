from datetime import datetime
from bot.types import Todo

from typing import List
from sqlalchemy import delete as sql_delete, false, update
from sqlmodel import select
from database.basic_database import BasicDatabase


class TodoDatabase(BasicDatabase):
    async def initialize(self) -> None:
        async with self.engine.begin() as s:
            await s.run_sync(Todo.metadata.create_all)

    async def get_todos(self, user_id: int) -> List[Todo]:
        stmt = select(Todo).where(Todo.user_id == user_id).order_by(Todo.todo_id)  # type: ignore
        async with self.get_session() as s:
            result = await s.execute(stmt)
            return list(result.scalars().all())

    async def get_unfinished_todos(self) -> List[Todo]:
        """供周期汇总提醒使用，不受按时提醒的发送记录影响。"""
        stmt = select(Todo).where(Todo.is_done == false()).order_by(Todo.user_id, Todo.todo_id)  # type: ignore
        async with self.get_session() as s:
            result = await s.execute(stmt)
            return list(result.scalars().all())

    async def get_due_reminders(self, now: datetime) -> List[Todo]:
        """获取尚未成功发送的到期待办。"""
        stmt = (
            select(Todo)
            .where(
                Todo.is_done == false(),
                Todo.reminder_sent_at.is_(None),  # type: ignore
                Todo.notify_time.is_not(None),  # type: ignore
                Todo.notify_time <= now,  # type: ignore
            )
            .order_by(Todo.notify_time, Todo.todo_id)  # type: ignore
        )
        async with self.get_session() as s:
            result = await s.execute(stmt)
            return list(result.scalars().all())

    async def mark_reminders_sent(self, todo_ids: list[int], sent_at: datetime) -> None:
        if not todo_ids:
            return
        async with self.get_session() as s:
            await s.execute(
                update(Todo)
                .where(Todo.todo_id.in_(todo_ids), Todo.reminder_sent_at.is_(None))  # type: ignore
                .values(reminder_sent_at=sent_at)
            )
            await s.commit()

    async def get_todo_by_id(self, todo_id: int) -> Todo | None:
        async with self.get_session() as s:
            res = await s.get(Todo, todo_id)
            if res:
                return res
            return None

    async def add_todo(self, todo: Todo) -> int:
        async with self.get_session() as s:
            s.add(todo)
            await s.commit()
            await s.refresh(todo)
            # 这里是主键，必定有，所以ignore
            return todo.todo_id  # type: ignore

    async def done(self, todo_id: int) -> None:
        async with self.get_session() as s:
            target_todo = await s.get(Todo, todo_id)
            if not target_todo:
                return None
            target_todo.is_done = True
            await s.commit()

    async def undone(self, todo_id: int) -> None:
        async with self.get_session() as s:
            target_todo = await s.get(Todo, todo_id)
            if not target_todo:
                return None
            target_todo.is_done = False
            await s.commit()

    async def delete(self, *, user_id: int, todo_id: int) -> bool:
        async with self.get_session() as s:
            result = await s.execute(
                sql_delete(Todo).where(Todo.todo_id == todo_id, Todo.user_id == user_id)  # type: ignore
            )
            await s.commit()
            return result.rowcount > 0  # type: ignore
