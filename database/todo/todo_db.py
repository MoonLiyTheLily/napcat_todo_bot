import logging
from pathlib import Path
from bot.types import Todo

from typing import List
from sqlmodel import select
from database.basic_database import BasicDatabase

logger = logging.getLogger(__name__)


class TodoDatabase(BasicDatabase):
    def __init__(self) -> None:
        super().__init__()

    async def initialize(self) -> None:
        async with self.engine.begin() as s:
            await s.run_sync(Todo.metadata.create_all)

    async def get_users(self) -> List[int]:
        stmt = select(Todo.user_id).distinct()
        async with self.get_session() as s:
            res = await s.execute(stmt)
            return list(res.scalars().all())

    async def get_todos(self, user_id: int | None) -> List[Todo]:
        stmt = select(Todo)
        if user_id:
            stmt = stmt.where(Todo.user_id == user_id)
        async with self.get_session() as s:
            result = await s.execute(stmt)
            return list(result.scalars().all())

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
            target_todo.is_done = True
            await s.commit()

    async def delete(self, todo_id: int) -> None:
        async with self.get_session() as s:
            target_todo = await s.get(Todo, todo_id)
            if not target_todo:
                return None
            await s.delete(target_todo)
            await s.commit()
