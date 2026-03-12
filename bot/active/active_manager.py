# 目前未使用
import asyncio
import logging
from bot.active.active_registry import active_registry


logger = logging.getLogger(__name__)


class ActiveLogicManager:
    """统一管理主动任务"""

    def __init__(self) -> None:
        self.active_tasks: list[asyncio.Task] = []

    def add_tasks(self):
        for name, task_registry_data in active_registry.items():
            if task_registry_data.function is not None:
                self.active_tasks.append(
                    asyncio.create_task(task_registry_data.function(), name=name)
                )

    async def run_tasks(self):
        try:
            done, _ = await asyncio.wait(
                self.active_tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                try:
                    res = task.result()
                    logger.info("任务结果: %s", res)
                except Exception as e:
                    logger.exception(" 任务出现错误: %s", e)

        except asyncio.CancelledError:
            logger.info("主动逻辑任务被取消，正在停止")
        # 待改进：添加重启逻辑
        finally:
            for task in self.active_tasks:
                if not task.done():
                    task.cancel()

            results = await asyncio.gather(*self.active_tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception) and not isinstance(
                    r, asyncio.CancelledError
                ):
                    logger.exception("主动逻辑任务退出时发生异常: %s", r)
