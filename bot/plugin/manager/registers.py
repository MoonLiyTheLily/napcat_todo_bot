from typing import Iterable, Iterator, Callable
from bot.plugin.basic_plugin import BasicPlugin

from bot.plugin.manager.plugin_registry import command_registry, CommandRegistryData
from bot.llm.llm_tool_registry import llm_tool_registry, LLMToolRegistryData
from bot.active.active_registry import active_registry, ActiveTaskRegistryData


def _marked_methods(
    instances: Iterable[BasicPlugin], marker: str
) -> Iterator[tuple[BasicPlugin, Callable]]:
    for instance in instances:
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if callable(attr) and hasattr(attr, marker):
                yield instance, attr


def register_commands(instances: Iterable[BasicPlugin]) -> None:
    """增量注册给定实例的命令方法。"""
    for instance, method in _marked_methods(instances, "__command_name__"):
        name = method.__command_name__
        if name in command_registry:
            raise ValueError(f"命令重复注册: {name}")
        command_registry[name] = CommandRegistryData(
            name=name, function=method, _class=type(instance)
        )


def register_llm_tools(instances: Iterable[BasicPlugin]) -> None:
    """增量注册给定实例的 LLM 工具。"""
    for _, method in _marked_methods(instances, "__llm_tool_name__"):
        name = method.__llm_tool_name__
        if name in llm_tool_registry:
            raise ValueError(f"LLM 工具重复注册: {name}")
        llm_tool_registry[name] = LLMToolRegistryData(
            name=name,
            description=method.__llm_tool_description__,
            function=method,
        )


def register_active_tasks(instances: Iterable[BasicPlugin]) -> None:
    """增量注册给定实例的主动任务。"""
    for _, method in _marked_methods(instances, "__active_task_name__"):
        name = method.__active_task_name__
        if name in active_registry:
            raise ValueError(f"主动任务重复注册: {name}")
        active_registry[name] = ActiveTaskRegistryData(
            interval=method.__active_task_interval__, func=method
        )
