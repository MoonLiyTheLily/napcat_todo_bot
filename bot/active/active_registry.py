import asyncio
from typing import Callable


class ActiveTaskRegistryData:
    def __init__(self, *, interval: int, func: Callable | None = None) -> None:
        self.function: Callable | None = func if callable(func) else None
        self.interval: int = interval


active_registry: dict[str, ActiveTaskRegistryData] = {}


def clear_active_registry():
    """全量清空，用于重载插件时"""

    active_registry.clear()


def register_active(task_name, interval: int):
    """声明主动任务，间隔单位为秒"""

    def decorator(f):
        async def wrapper(self, **kwargs):
            while True:
                await f(self, **kwargs)
                await asyncio.sleep(interval)

        wrapper.__active_task_name__ = task_name
        wrapper.__active_task_interval__ = interval

        return wrapper

    return decorator
