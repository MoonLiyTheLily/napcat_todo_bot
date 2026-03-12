import asyncio
import json
import logging
import websockets
import colorlog
from bot.apis.send_message import sender
from bot.handlers import UniversalHandler
from bot.config.config import DEFAULT_CONFIG
from bot.plugin.manager.plugin_manager import PluginManager
from bot.active.active_manager import ActiveLogicManager

logger = logging.getLogger(__name__)

colored_log_handler = colorlog.StreamHandler()
colored_log_handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(asctime)s [%(log_color)s%(levelname)s%(reset)s] [%(name)s] - %(message)s",
        # " %(log_color)s%(levelname)s%(reset)s - %(message)s",
        datefmt="%m-%d %H:%M:%S",
        # datefmt="%m-%d %I:%M:%S %p",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
)
logging.basicConfig(
    level=logging.INFO,
    # format="%(asctime)s [%(levelname)s] [%(name)s] : %(message)s",
    # datefmt="%m-%d %H:%M:%S",
    handlers=[
        colored_log_handler
        # logging.StreamHandler(sys.stdout),
        # logging.FileHandler("logs/app.log", encoding="utf-8"),
    ],
)


def _log_task_result(task: asyncio.Task):
    """记录异步任务的结果"""
    try:
        result = task.result()
        logger.info("异步任务完成，结果: %s", result)
    except asyncio.CancelledError:
        logger.info("异步任务被取消")
    except Exception as e:
        logger.exception("异步任务出现错误: %s", str(e))


async def handle_event(websocket):
    """总Handler

    :param websocket: 说明
    """
    sender.websocket = websocket
    universal_handler = UniversalHandler()
    active_task_manager = ActiveLogicManager()
    active_task_manager.add_tasks()
    active_task_manager_task = asyncio.create_task(active_task_manager.run_tasks())

    # Gemimi加的
    # 强引用集合，防止 create_task 创建的后台任务被垃圾回收导致意外中断
    background_tasks = set()

    try:
        async for message in websocket:
            try:
                event: dict = json.loads(message)
            except json.JSONDecodeError:
                logger.warning("收到非JSON格式消息，已忽略")
                continue

            # 处理消息事件
            if event.get("post_type") == "message":
                task = asyncio.create_task(universal_handler.handle(event))
                background_tasks.add(task)

                # Gemini加的
                # 任务完成后从集合中移除，并统一打印日志
                task.add_done_callback(background_tasks.discard)
                # task.add_done_callback(_log_task_result)
    except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
        logger.info("WebSocket连接已关闭")
    finally:
        active_task_manager_task.cancel()
        await active_task_manager_task


async def main():
    """主函数"""
    # 初始化插件管理器
    p = PluginManager()
    p.load()
    server = await websockets.serve(
        handle_event,
        DEFAULT_CONFIG["websocket_host"],
        DEFAULT_CONFIG["websocket_port"],
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
