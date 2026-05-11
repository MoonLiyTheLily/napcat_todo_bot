import json
from typing import Any


class ReplyMessage:
    def __init__(self) -> None:
        self.action: str = "send_private_msg"
        self.user_id: int | None = None
        self.message: list[dict[str, Any]] = []

    def to(self, _user_id: int) -> "ReplyMessage":
        self.user_id = _user_id
        return self

    def text(self, _text: str) -> "ReplyMessage":
        self.message.append(
            {
                "type": "text",
                "data": {"text": _text},
            }
        )
        return self

    def image(self, _file_path: str, _summary: str = "图片") -> "ReplyMessage":
        self.message.append(
            {
                "type": "image",
                "data": {
                    "summary": _summary,
                    "path": _file_path,
                },
            }
        )
        return self

    def build(self) -> str:
        assert self.user_id is not None, "user_id不能为空"
        reply = {
            "action": self.action,
            "params": {
                "user_id": self.user_id,
                "message": self.message,
            },
        }
        return json.dumps(reply, ensure_ascii=False)


def create_reply() -> ReplyMessage:
    """创建回复消息

    :param to: 回复的目标用户ID
    :type to: str
    :return: 回复消息对象
    :rtype: ReplyMessage
    """
    reply = ReplyMessage()
    return reply
