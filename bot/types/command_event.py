class CommandEvent:
    """命令事件类，提供一个标准化的纯文本命令封装"""

    def __init__(
        self,
        _user_id: int,
        _command: str = "",
        _parameter: list[str] | None = None,
        _user_send_time: str = "",
    ) -> None:
        self.user_id: int = _user_id
        self.command: str = _command
        self.user_send_time: str = _user_send_time
        # OneBot消息结构里，这个发送时间本来是 UNIX Timestamp
        # 默认创建的时候，都采用"%Y-%m-%d %H:%M:%S"格式格式化
        if _parameter is None:
            self.parameters: list[str] = []
        else:
            self.parameters = _parameter

    def __repr__(self) -> str:
        return f"<CommandEvent from User: {self.user_id} Command:{self.command} Parameter:{self.parameters}>"

    def is_empty(self) -> bool:
        """判断命令事件是不是空的"""
        if self.user_id is None or self.command == "" or self.parameters is None:
            return True
        return False
