from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass(frozen=True)
class ActiveTaskRegistryData:
    function: Callable[[], Awaitable[None]]
    interval: float


active_registry: dict[str, ActiveTaskRegistryData] = {}


def clear_active_registry() -> None:
    """清空注册表，供插件重载使用。"""
    active_registry.clear()


def register_active(task_name: str, interval: float):
    """声明周期任务。interval 的单位为秒，任务启动后立即执行一次。"""
    if interval <= 0:
        raise ValueError(f"主动任务 {task_name} 的间隔必须大于零")

    def decorator(function):
        function.__active_task_name__ = task_name
        function.__active_task_interval__ = interval
        return function

    return decorator
