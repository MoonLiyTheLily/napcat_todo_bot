import asyncio
import logging
from bot.active.active_registry import ActiveTaskRegistryData, active_registry

logger = logging.getLogger(__name__)


class ActiveLogicManager:
    """管理周期任务的启动、重试和停止"""

    def __init__(self) -> None:
        self.tasks: dict[str, asyncio.Task[None]] = {}

    async def _run_task(self, name: str, data: ActiveTaskRegistryData) -> None:
        while True:
            try:
                await data.function()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("主动任务 %s 执行失败，3 秒后重试", name)
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(data.interval)

    def run(self) -> None:
        """启动尚未运行的注册任务，将其加入 self.tasks"""
        for name, data in active_registry.items():
            if name not in self.tasks or self.tasks[name].done():
                self.tasks[name] = asyncio.create_task(
                    self._run_task(name, data), name=name
                )

    async def stop(self) -> None:
        tasks = list(self.tasks.values())
        self.tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
