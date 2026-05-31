import asyncio
import json
import logging
import websockets
from bot.handlers import UniversalHandler
from bot.plugin.manager.plugin_manager import PluginManager
from bot.active.active_manager import ActiveLogicManager
from bot.apis.plugin_context import PluginContext
from bot.config.config import config

logger = logging.getLogger(__name__)


class Core:
    """核心类，负责初始化所有的组件，并分发消息"""

    def __init__(self) -> None:
        self.plugin_manager = None
        self.universal_handler = None
        self.active_task_manager = None
        self.plugin_context = None
        self.active_task_manager_task = None

    async def initialize(self):
        # 插件管理器
        self.plugin_manager = PluginManager()
        await self.plugin_manager.load()

        # 插件上下文
        self.plugin_context = PluginContext(config, self.plugin_manager)

        # 主消息处理器
        self.universal_handler = UniversalHandler(self.plugin_context)

        # 主动任务管理器
        self.active_task_manager = ActiveLogicManager()
        self.active_task_manager.add_tasks()

        # 开始运行主动任务
        self.active_task_manager_task = asyncio.create_task(
            self.active_task_manager.run_tasks()
        )

    def check_initialize(self):
        return (
            self.plugin_manager is not None
            and self.universal_handler is not None
            and self.active_task_manager is not None
            and self.plugin_context is not None
            and self.active_task_manager_task is not None
        )

    async def handle(self, websocket):
        if not self.check_initialize():
            logger.warning("Core没有正确初始化。")
            return
        self.plugin_context.message_sender.websocket = websocket  # type: ignore
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
                    # 在前面检查是否已经完整初始化，此处用ignore避免类型检查继续提示
                    task = asyncio.create_task(self.universal_handler.handle(event))  # type: ignore
                    background_tasks.add(task)

                    # Gemini加的
                    # 任务完成后从集合中移除，并统一打印日志
                    task.add_done_callback(background_tasks.discard)
                    # task.add_done_callback(_log_task_result)
        except (websockets.ConnectionClosedError, websockets.ConnectionClosed):
            logger.info("WebSocket连接已关闭")
        finally:
            # 在前面检查是否已经完整初始化，此处用ignore避免类型检查继续提示
            self.active_task_manager_task.cancel()  # type: ignore
            await self.active_task_manager_task  # type: ignore
