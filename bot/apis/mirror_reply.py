import json
import logging
from bot.apis.send_message import sender

logger = logging.getLogger(__name__)


# 本函数保留了最原始的生成返回消息逻辑，以供有关消息模块编写时参考
async def create_mirror_reply(event: dict, mirror_tip: bool = False):
    """按照用户发送的消息，生成完全一样的回复

    :param event: 已经转化成dict的NapCatQQ事件列表
    :type event: dict
    :param mirror_tip: 是否显示提示信息（也就是“你说了:<换行符>”）
    :type mirror_tip: bool
    """
    assert event.get("post_type") == "message", logger.warning("错误参数")

    user_id = event["user_id"]
    # 给出消息链里的消息类型
    logger.info("=== Message List Start ===")
    i = 1
    for msg in event["message"]:
        logger.info(
            "本批次第%d条类型为%s消息: %s (来自%s)",
            i,
            msg["type"],
            msg["data"],
            user_id,
        )
        i += 1
    logger.info("=== Message List End ===")
    # 创建reply列表
    reply_messages = []
    for msg in event["message"]:
        if msg["type"] == "text":
            reply_messages.append(
                {
                    "type": "text",
                    "data": {"text": msg["data"]["text"]},
                }
            )
        if msg["type"] == "image":
            reply_messages.append(
                {
                    "type": "image",
                    "data": {
                        "summary": msg["data"]["summary"],
                        "path": msg["data"]["url"],
                    },
                }
            )

    if mirror_tip:
        reply_messages.insert(
            0,
            {
                "type": "text",
                "data": {"text": "你说了:\n"},
            },
        )
    reply = {
        "action": "send_private_msg",
        "params": {
            "user_id": user_id,
            "message": reply_messages,
        },
    }
    await sender.send(json.dumps(reply, ensure_ascii=False))
    # return json.dumps(reply, ensure_ascii=False)
