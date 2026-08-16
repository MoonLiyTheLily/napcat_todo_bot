# 目前未使用
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
    """注册一定时间触发一次的主动任务，interval单位是秒"""
    active_registry.update({task_name: ActiveTaskRegistryData(interval=interval)})

    def decorator(f):
        async def wrapper(self, **kwargs):
            while True:
                await f(self, **kwargs)
                await asyncio.sleep(interval)

        wrapper.__active_task_name__ = task_name

        return wrapper

    return decorator
