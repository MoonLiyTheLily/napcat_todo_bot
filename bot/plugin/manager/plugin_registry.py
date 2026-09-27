from dataclasses import dataclass
from typing import Callable


@dataclass
class CommandRegistryData:
    name: str
    function: Callable | None = None
    _class: type | None = None


command_registry: dict[str, CommandRegistryData] = {}


def register_command(command: str):
    """指定命令，将函数注册为命令处理器

    返回一个装饰器，这个装饰器会给函数添加一个__command_name__属性
    """

    def decorator(func):
        func.__command_name__ = command
        return func

    return decorator


def clear_command_registry():
    """清空命令注册表。"""

    command_registry.clear()
