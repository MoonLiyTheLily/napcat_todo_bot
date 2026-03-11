import pydantic


class TodoItem(pydantic.BaseModel):
    """Todo事项类，包含了基本的Todo事项属性"""

    database_id: int
    user_id: int
    content: str
    is_done: bool
    user_create_time: str
    update_time: str
    complete_time: str

    def get_list_string(self):
        """获取用于聊天显示的字符串

        :param self: 说明
        """
        completed = "✅" if self.is_done else "❎"
        return f"{completed} | {self.content}\n(创建时间: {self.user_create_time})"
