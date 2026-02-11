import logging
from datetime import datetime
from bot.types import CommandEvent

logger = logging.getLogger(__name__)


def is_command(event: dict) -> bool:
    """
    判断当前消息事件是不是一个命令，返回bool

    :param event: 已经转化成dict的NapCatQQ事件列表
    :type event: dict
    """
    if event.get("post_type") == "message":
        msg = event["message"][0]
        # 只有text才识别是不是命令
        if msg["type"] == "text":
            msg_string: str = msg["data"]["text"]
            msg_split = msg_string.split()
            if msg_split[0][0] == "/":
                return True
            else:
                return False
        else:
            return False
    return False


def command_resolver(event: dict):
    """
    解析命令，返回CommandEvent

    dict结构为{"command":<命令名字>,"parameters":<一个list，含有当前文本段剩下所有的paramater，按照空格split>}

    :param event: 已经转化成dict的NapCatQQ事件列表
    :type event: dict
    """
    if event.get("post_type") == "message":
        # 简化，只识别第一个文本消息
        msg = event["message"][0]
        # 只有text才识别是不是命令
        if msg["type"] == "text":
            msg_string: str = msg["data"]["text"]
            logger.info("本条消息：%s", msg_string)
            msg_split = msg_string.split()
            if msg_split[0][0] == "/":
                logger.info("解析成功，返回命令%s", {msg_split[0][1:]})
                return CommandEvent(
                    event["user_id"],
                    msg_split[0][1:],
                    msg_split[1:],
                    datetime.fromtimestamp(event["time"]).strftime("%Y-%m-%d %H:%M:%S"),
                )
            else:
                logger.info("解析失败")
                return CommandEvent()
        else:
            logger.info("非文本消息，不是命令，解析")
            return CommandEvent()
    else:
        return CommandEvent()


def command_resolver_dict(event: dict):
    """
    解析命令，如果成功，返回一个dict，或者None

    dict结构为{"command":<命令名字>,"parameters":<一个list，含有当前文本段剩下所有的paramater，按照空格split>}

    :param event: 已经转化成dict的NapCatQQ事件列表
    :type event: dict
    """
    if event.get("post_type") == "message":
        # 简化，只识别第一个文本消息
        msg = event["message"][0]
        # 只有text才识别是不是命令
        if msg["type"] == "text":
            msg_string: str = msg["data"]["text"]
            logger.info("本条消息：%s", msg_string)
            msg_split = msg_string.split()
            if msg_split[0][0] == "/":
                logger.info("解析成功，返回命令%s", {msg_split[0][1:]})
                return {
                    "command": msg_split[0][1:],
                    "parameters": msg_split[1:],
                }
            else:
                logger.info("解析失败")
                return None
        else:
            logger.info("非文本消息，不是命令")
            return None
    else:
        return None
