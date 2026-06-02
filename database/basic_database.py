from pathlib import Path
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


class BasicDatabase:
    def __init__(self) -> None:
        self.db_path = Path(__file__).parent / "test.db"
        self.database_link = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = create_async_engine(self.database_link)
        self.session_maker = async_sessionmaker(self.engine, class_=AsyncSession)

    async def initialize(self) -> None:
        raise NotImplementedError

    @asynccontextmanager
    async def get_session(self):
        async with self.session_maker() as s:
            yield s
