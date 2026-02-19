import asyncio
import json
import logging
import sys
import websockets
from bot.handlers import UniversalHandler
from bot.types.todo_item import TodoItem
from database import TodoDatabase

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] : %(message)s",
    datefmt="%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler("logs/app.log", encoding="utf-8"),
    ],
)


async def active_actions(websocket):
    """
    统一托管所有“主动逻辑”后台任务：
    - 在这里创建任务
    - 在 finally 中统一 cancel + await 回收
    """
    tasks: list[asyncio.Task] = []
    try:
        tasks.append(
            asyncio.create_task(todo_notifier(websocket), name="todo_notifier")
        )

        # 主动逻辑任务，都在此处 append
        # tasks.append(asyncio.create_task(other_active_job(websocket), name="other_active_job"))

        # 等待：只要有一个任务异常退出，就触发清理（FIRST_EXCEPTION）
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        # 如果有任务异常结束，把异常抛出去（让日志更集中）
        for t in done:
            exc = t.exception()
            if exc is not None:
                raise exc

        # 正常情况下（你的任务通常是 while True），这里一般不会走到
        return None

    except asyncio.CancelledError:
        logger.info("active_actions 被取消，开始停止所有主动逻辑任务")
        raise
    finally:
        # 统一取消 + 回收，避免泄漏/孤儿任务
        for t in tasks:
            if not t.done():
                t.cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
                logger.exception("主动逻辑任务退出时发生异常: %s", r)


def _log_task_result(task: asyncio.Task):
    """
    记录异步任务的结果
    :param task: 说明
    :type task: asyncio.Task
    """
    try:
        result = task.result()
        logger.info("异步任务完成，结果: %s", result)
    except asyncio.CancelledError:
        logger.info("异步任务被取消")
    except Exception as e:
        logger.exception("异步任务出现错误: %s", str(e))


async def todo_notifier(websocket):
    """
    todo_notifier 的 Docstring
    """
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
                        reply = {
                            "action": "send_private_msg",
                            "params": {
                                "user_id": user_id,
                                "message": message,
                            },
                        }
                        await websocket.send(json.dumps(reply, ensure_ascii=False))
                        logger.info("已发送待办事项通知给用户%s", user_id)
            db.close()
            await asyncio.sleep(1800)  # 每30分钟检查一次
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


async def handle_event(websocket):
    """
    handle_event 的 Docstring

    :param websocket: 说明
    """
    universal_handler = UniversalHandler()
    active_task = asyncio.create_task(active_actions(websocket))
    active_task.add_done_callback(_log_task_result)
    try:
        async for message in websocket:
            event: dict = json.loads(message)
            # 处理消息事件
            if event.get("post_type") == "message":
                try:
                    reply = await universal_handler.handle(event)
                except Exception as e:
                    logger.exception("处理消息事件时出现错误: %s", str(e))
                    reply = None
                if reply is not None:
                    try:
                        await websocket.send(reply)
                    except (
                        websockets.ConnectionClosedError,
                        websockets.ConnectionClosed,
                    ):
                        logger.error("发送回复时出现错误: Websocket连接已关闭")
    except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
        logger.info("WebSocket连接已关闭")
    finally:
        active_task.cancel()
        await active_task


async def main():
    """
    main 的 Docstring
    """
    server = await websockets.serve(
        handle_event,
        "127.0.0.1",
        8000,
        subprotocols=[],  # 建议加上，兼容性更好
    )
    logger.info("WebSocket 服务已启动")
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        server.close()
        await server.wait_closed()
        logger.info("WebSocket 服务已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已终止")
