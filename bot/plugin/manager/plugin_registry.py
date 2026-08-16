import sys
from dataclasses import dataclass
from typing import Callable
from bot.plugin.basic_plugin import BasicPlugin
from bot.llm.llm_tool_registry import llm_tool_registry
from bot.active.active_registry import active_registry


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
    """用于重载插件的时候提前clear"""

    command_registry.clear()


def auto_register() -> list[BasicPlugin]:
    """自动扫描import的所有插件，并注册里面的方法，返回插件实例列表"""

    command_registry.clear()
    instances: list[BasicPlugin] = []
    plugin_class_list = BasicPlugin.__subclasses__()
    for cls in plugin_class_list:

        # 验证该类是否是模块中当前最新（存活）的类，防止重载带来的旧类滞留
        module = sys.modules.get(cls.__module__)
        if not module or getattr(module, cls.__name__, None) is not cls:
            continue

        # 实例化这个类，然后注册它底下所有的命令
        instance = cls()
        instances.append(instance)
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if not callable(attr):
                continue
            if hasattr(attr, "__command_name__"):
                name = attr.__command_name__
                command_registry[name] = CommandRegistryData(
                    name=name, function=attr, _class=cls
                )
            elif hasattr(attr, "__llm_tool_name__"):
                name = attr.__llm_tool_name__
                if name in llm_tool_registry:
                    llm_tool_registry[name].function = attr
            elif hasattr(attr, "__active_task_name__"):
                name = attr.__active_task_name__
                if name in active_registry:
                    active_registry[name].function = attr

    return instances
