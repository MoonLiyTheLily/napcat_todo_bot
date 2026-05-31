from sqlmodel import SQLModel, Field
from datetime import datetime


class LastMessageRecord(SQLModel, table=True):
    __tablename__: str = "last_message_record"
    user_id: int = Field(primary_key=True)
    send_time: datetime
