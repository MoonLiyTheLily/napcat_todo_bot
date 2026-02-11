class TodoItem:
    """
    Todo事项类，包含了基本的Todo事项属性
    """

    def __init__(
        self,
        _database_id: int,
        _user_id: str,
        _content: str,
        _is_done: bool,
        _user_create_time: str,
        _update_time: str,
        _complete_time: str,
    ) -> None:
        self.database_id = _database_id
        self.user_id = _user_id
        self.content = _content
        self.is_done = _is_done
        self.user_create_time = _user_create_time
        self.update_time = _update_time
        self.complete_time = _complete_time

    def get_list_string(self):
        """
        获取用于聊天显示的字符串

        :param self: 说明
        """
        completed = "✅" if self.is_done else "❎"
        return f"{completed} | {self.content}\n(创建时间: {self.user_create_time})"

    # def get_database_id(self) -> int:
    #     return self.database_id

    # def get_user_id(self) -> str:
    #     return self.user_id

    # def get_content(self) -> str:
    #     return self.content

    # def get_is_done(self) -> bool:
    #     return self.is_done

    # def get_user_create_time(self) -> str:
    #     return self.user_create_time

    # def get_update_time(self) -> str:
    #     return self.update_time

    # def get_complete_time(self) -> str:
    #     return self.complete_time
