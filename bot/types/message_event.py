# 本类未使用
class MessageEvent:
    """
    标准消息事件类，提供一个处理消息的封装
    """

    def __init__(self) -> None:
        self.time: int = 0
        self.post_type: str = "None"
        self.self_id: int = 0

        self.message_type: str = "None"
        self.sub_type: str = "None"
        self.message_id: int = 0
        self.user_id: int = 0
        self.message = None

    def dump_to_json(self):
        return None
