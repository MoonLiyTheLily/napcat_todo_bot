import pydantic


class TodoItem(pydantic.BaseModel):
    """Todo事项类，包含了基本的Todo事项属性"""

    database_id: int
    user_id: int
    content: str
    is_done: bool
    user_create_time: str
    update_time: str
    complete_time: str | None
    notify_time: str | None

    def get_list_string(self):
        """获取用于聊天显示的字符串

        :param self: 说明
        """
        completed = "✅" if self.is_done else "❎"
        result = f"{completed} | {self.content}\n(创建时间: {self.user_create_time})"
        if self.complete_time is not None or self.complete_time == "":
            result += f"\n(完成时间 {self.complete_time})"
        if self.notify_time is not None or self.notify_time == "":
            result += f"\n(提醒时间 {self.notify_time})"
        return result
