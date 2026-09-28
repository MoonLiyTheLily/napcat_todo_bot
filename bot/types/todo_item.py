from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Column, DateTime, Index, func, text


class Todo(SQLModel, table=True):
    __tablename__: str = "todo"
    __table_args__ = (
        Index("ix_todo_user_order", "user_id", "todo_id"),
        Index(
            "ix_todo_open_user_order",
            "user_id",
            "todo_id",
            sqlite_where=text("is_done = 0"),
        ),
        Index(
            "ix_todo_due_reminder",
            "notify_time",
            "todo_id",
            sqlite_where=text(
                "is_done = 0 AND reminder_sent_at IS NULL AND notify_time IS NOT NULL"
            ),
        ),
    )

    todo_id: int | None = Field(default=None, primary_key=True)
    user_id: int
    content: str
    is_done: bool = Field(default=False)
    create_time: datetime = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now()),
    )
    update_time: datetime = Field(
        default=None,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now()),
    )
    complete_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    notify_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )
    reminder_sent_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, nullable=True)
    )

    def get_list_string(self):
        """获取用于聊天显示的字符串

        :param self: 说明
        """
        completed = "✅" if self.is_done else "❎"
        result = f"{completed} | {self.content}\n(创建时间: {self.create_time})"
        if self.complete_time is not None:
            result += f"\n(完成时间 {self.complete_time})"
        if self.notify_time is not None:
            result += f"\n(提醒时间 {self.notify_time})"
        return result
