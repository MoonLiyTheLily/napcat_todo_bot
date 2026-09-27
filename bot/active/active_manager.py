import asyncio
import logging
from bot.active.active_registry import active_registry

logger = logging.getLogger(__name__)


class ActiveLogicManager:
    """统一管理主动任务"""

    def __init__(self) -> None:
        self.active_tasks: list[asyncio.Task] = []
        self.main_task: asyncio.Task | None = None

    def add_tasks(self):
        for name, task_registry_data in active_registry.items():
            if task_registry_data.function is not None:
                self.active_tasks.append(
                    asyncio.create_task(task_registry_data.function(), name=name)
                )

    async def _run_tasks(self):
        while self.active_tasks:
            done, _ = await asyncio.wait(
                self.active_tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                self.active_tasks.remove(task)
                try:
                    res = task.result()
                    logger.info("任务结果: %s", res)
                except asyncio.CancelledError:
                    logger.info("主动逻辑任务%s被取消", task.get_name())
                except Exception as e:
                    logger.exception("任务出现错误: %s，3秒后重启", e)
                    await asyncio.sleep(3)
                    data = active_registry[task.get_name()]
                    if data.function is not None:
                        self.active_tasks.append(
                            asyncio.create_task(data.function(), name=task.get_name())
                        )

    def run(self):
        if self.main_task is not None and not self.main_task.done():
            return
        if not self.active_tasks:
            self.add_tasks()
        self.main_task = asyncio.create_task(self._run_tasks())

    async def stop(self) -> None:
        """先停止任务监督器，再取消并等待所有主动任务。"""
        if self.main_task is not None:
            self.main_task.cancel()
            await asyncio.gather(self.main_task, return_exceptions=True)
            self.main_task = None

        tasks = self.active_tasks.copy()
        self.active_tasks.clear()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
