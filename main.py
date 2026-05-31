import asyncio
import logging
import websockets
import colorlog
from bot.config.config import config
from bot.core import Core

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


async def main() -> None:
    """主函数"""
    # 初始化
    core = Core()
    await core.initialize()

    server = await websockets.serve(
        core.handle,
        config.get("websocket_host"),
        config.get("websocket_port"),
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
