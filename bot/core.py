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
        self._connection = None
        self._connection_lock = asyncio.Lock()

    async def initialize(self):
        # 插件管理器
        self.plugin_manager = PluginManager()
        await self.plugin_manager.load()

        # 主动任务管理器
        self.active_task_manager = ActiveLogicManager()

        # 插件上下文
        self.plugin_context = PluginContext(
            config, self.plugin_manager, self.reload_plugins
        )

        # 主消息处理器
        self.universal_handler = UniversalHandler(self.plugin_context)

    def check_initialize(self):
        return (
            self.plugin_manager is not None
            and self.universal_handler is not None
            and self.active_task_manager is not None
            and self.plugin_context is not None
        )

    async def shutdown(self) -> None:
        """停止主动任务后卸载插件。"""
        try:
            async with self._connection_lock:
                if self.active_task_manager is not None:
                    await self.active_task_manager.stop()
                if self._connection is not None and self.plugin_context is not None:
                    self.plugin_context.message_sender.unbind(self._connection)
                    self._connection = None
        finally:
            if self.plugin_manager is not None:
                await self.plugin_manager.shutdown()
            if self.universal_handler is not None:
                await self.universal_handler.last_message_db.close()

    async def reload_plugins(self) -> None:
        """按顺序停止旧任务、重载插件，再启动新任务。"""
        async with self._connection_lock:
            # 此处假设已完成初始化
            await self.active_task_manager.stop()  # type: ignore
            await self.plugin_manager.reload()  # type: ignore
            if self._connection is not None:
                self.active_task_manager.run()  # type: ignore

    async def handle(self, websocket) -> None:
        if not self.check_initialize():
            logger.warning("Core没有正确初始化。")
            return
        async with self._connection_lock:
            if self._connection is not None:
                logger.warning("已有活动连接，拒绝第二个 WebSocket 连接")
                await websocket.close(code=1013, reason="已有活动连接")
                return
            self._connection = websocket
            self.plugin_context.message_sender.bind(websocket)  # type: ignore
            self.active_task_manager.run()  # type: ignore
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

                    def on_done(done_task: asyncio.Task):
                        background_tasks.discard(done_task)
                        if not done_task.cancelled():
                            error = done_task.exception()
                            if error is not None:
                                logger.error(
                                    "处理消息时发生错误",
                                    exc_info=(type(error), error, error.__traceback__),
                                )

                    task.add_done_callback(on_done)

        except websockets.ConnectionClosedError, websockets.ConnectionClosed:
            logger.info("WebSocket连接已关闭")
        finally:
            for task in background_tasks:
                task.cancel()
            await asyncio.gather(*background_tasks, return_exceptions=True)
            async with self._connection_lock:
                if self._connection is websocket:
                    await self.active_task_manager.stop()  # type: ignore
                    self.plugin_context.message_sender.unbind(websocket)  # type: ignore
                    self._connection = None
