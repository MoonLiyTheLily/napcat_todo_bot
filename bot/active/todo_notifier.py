import logging
import asyncio
import websockets
from database import TodoDatabase
from bot.apis.create_reply import create_reply
from bot.apis.send_message import sender
from bot.types import TodoItem
from bot.config.config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


async def todo_notifier():
    """Todo定时通知函数"""
    notify_interval = DEFAULT_CONFIG["active"]["todo"]["notify_interval"]
    while True:
        try:
            db = TodoDatabase()
            logger.info("检查待办事项通知")
            users = db.check_all_user()
            if users is not None:
                for user_id in users:
                    user_todos = []
                    todo_items = db.check_todo(user_id)
                    assert todo_items is not None
                    for item in todo_items:
                        assert isinstance(item, TodoItem)
                        if not item.is_done:
                            user_todos.append(item.get_list_string())
                    if len(user_todos) > 0:
                        message = "您有以下待办事项未完成：\n" + "\n".join(user_todos)
                        reply = create_reply().to(user_id).text(message).build()
                        await sender.send(reply)
                        logger.info("已发送待办事项通知给用户%s", user_id)
            db.close()
            await asyncio.sleep(notify_interval)  # 默认半小时检查一次
        except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
            logger.error("WebSocket连接已关闭，停止待办事项通知")
            return
        except asyncio.CancelledError:
            logger.info("待办事项通知任务已取消")
            raise
        except Exception as e:
            logger.exception("待办事项通知出现错误: %s，将在1分钟后重试", str(e))
            raise
        finally:
            if db is not None:
                db.close()
