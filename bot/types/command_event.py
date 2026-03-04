class CommandEvent:
    """命令事件类，提供一个标准化的纯文本命令封装"""

    def __init__(
        self,
        _user_id: int,
        _command: str = "",
        _parameter: list[str] | None = None,
        _user_send_time="",
    ) -> None:
        self.user_id = _user_id
        self.command = _command
        self.user_send_time = _user_send_time
        if _parameter is None:
            self.parameters = []
        else:
            self.parameters = _parameter

    def __repr__(self) -> str:
        return f"<CommandEvent from User: {self.user_id} Command:{self.command} Parameter:{self.parameters}>"

    def is_empty(self) -> bool:
        """判断命令事件是不是空的

        :param self: 说明
        :return: 说明
        :rtype: bool
        """
        if self.user_id is None or self.command == "" or self.parameters is None:
            return True
        return False
