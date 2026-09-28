import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
import importlib
import sys
from types import ModuleType
from typing import Literal

import bot.plugin.manager.plugin_path as plugin_path
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.registers import (
    register_commands,
    register_llm_tools,
    register_active_tasks,
)
from bot.plugin.manager.plugin_registry import clear_command_registry
from bot.llm.llm_tool_registry import clear_llm_tool_registry
from bot.active.active_registry import clear_active_registry

logger = logging.getLogger(__name__)


@dataclass
class PluginData:
    name: str
    file_path: Path
    module_path: str
    builtin: bool
    module: ModuleType | None = None
    instances: list[BasicPlugin] = field(default_factory=list)
    status: Literal["discovered", "imported", "ready", "failed"] = "discovered"
    error: str | None = None


class PluginManager:
    def __init__(self) -> None:
        self.plugins: dict[str, PluginData] = {}

    @staticmethod
    def _get_module_file(path: str) -> list[dict[str, str]]:
        modules = []
        dir_list = os.listdir(path)

        for d in dir_list:
            if os.path.isdir(os.path.join(path, d)):
                if os.path.exists(os.path.join(path, d, "main.py")):
                    modules.append(
                        {
                            "name": d,
                            "module_name": "main",
                            "path": os.path.join(path, d, "main.py"),
                        }
                    )
                elif os.path.exists(os.path.join(path, d, f"{d}.py")):
                    modules.append(
                        {
                            "name": d,
                            "module_name": d,
                            "path": os.path.join(path, d, f"{d}.py"),
                        }
                    )
                else:
                    print(f"目录{d}下未找到main.py或{d}.py.")
        return modules

    def _get_plugin_modules(self) -> dict[str, list[dict[str, str]]]:
        builtin_list = self._get_module_file(plugin_path.get_builtin_plugin_path())
        other_list = []
        if os.path.exists(plugin_path.get_other_plugin_path()):
            other_list = self._get_module_file(plugin_path.get_other_plugin_path())
        return {
            "builtin": builtin_list,
            "other": other_list,
        }

    def _initialize_plugins(self) -> None:
        """实例化入口模块显式声明的插件类。"""
        clear_command_registry()
        clear_llm_tool_registry()
        clear_active_registry()
        # 防止重复实例化、注册命令等
        seen_classes: set[type[BasicPlugin]] = set()

        for plugin in self.plugins.values():
            try:
                if plugin.module is None:
                    raise ValueError("插件模块尚未导入")
                plugin_classes = getattr(plugin.module, "PLUGIN_CLASSES", None)
                if not isinstance(plugin_classes, (list, tuple)) or not plugin_classes:
                    raise ValueError(
                        "入口模块必须提供非空的 PLUGIN_CLASSES 列表或 Tuple"
                    )

                for cls in plugin_classes:
                    if not isinstance(cls, type) or not issubclass(cls, BasicPlugin):
                        raise TypeError(f"无效的插件类: {cls!r}")
                    if cls in seen_classes:
                        raise ValueError(f"插件类重复声明: {cls.__name__}")
                    seen_classes.add(cls)
                    # 初始化
                    plugin.instances.append(cls())

            except Exception as exc:
                plugin.status = "failed"
                plugin.error = str(exc)
                raise

    async def load(self) -> None:
        """
        加载插件（异步初始化）
        包括 import 插件和实例化插件类两个部分
        """

        self.plugins.clear()

        plugin_module_list = self._get_plugin_modules()
        # source 为 "builtin" 或 "other"
        for source, discovered_plugins in plugin_module_list.items():
            for discovered in discovered_plugins:
                # 加入元数据
                module_path = f"bot.plugin.{source}.{discovered['name']}.{discovered['module_name']}"
                plugin = PluginData(
                    name=discovered["name"],
                    file_path=Path(discovered["path"]),
                    module_path=module_path,
                    builtin=(source == "builtin"),
                )
                self.plugins[f"{source}:{plugin.name}"] = plugin
                # 导入此模块
                try:
                    plugin.module = importlib.import_module(module_path)
                    plugin.status = "imported"
                except Exception as exc:
                    plugin.status = "failed"
                    plugin.error = str(exc)
                    raise
        self._initialize_plugins()
        # 只有插件实例化、初始化成功，才对外注册其方法
        for plugin in self.plugins.values():
            for instance in plugin.instances:
                try:
                    await instance.initialize()
                except Exception as exc:
                    plugin.status = "failed"
                    plugin.error = f"{type(instance).__name__}: {exc}"
                    logger.exception("插件 %s 异步初始化失败", type(instance).__name__)
            if plugin.status != "failed":
                try:
                    register_commands(plugin.instances)
                    register_llm_tools(plugin.instances)
                    register_active_tasks(plugin.instances)
                    plugin.status = "ready"
                except Exception as exc:
                    plugin.status = "failed"
                    plugin.error = str(exc)
                    raise

    async def reload(self) -> None:
        """卸载旧实例，重载入口及其子模块，再重建注册表。"""
        module_names: set[str] = set()
        for plugin in self.plugins.values():
            module_names.add(plugin.module_path)
            prefix = plugin.module_path.rsplit(".", 1)[0] + "."
            module_names.update(name for name in sys.modules if name.startswith(prefix))

        await self.shutdown()
        try:
            for name in sorted(
                module_names, key=lambda name: name.count("."), reverse=True
            ):
                importlib.reload(sys.modules[name])
        except ModuleNotFoundError as e:
            logger.exception("未找到目标插件模块: %s", e)
            raise
        except Exception as e:
            logger.exception("重载错误: %s", e)
            raise

        await self.load()

    async def shutdown(self) -> None:
        """按加载的逆序卸载插件，并清理注册表。"""
        for plugin in reversed(list(self.plugins.values())):
            for instance in reversed(plugin.instances):
                try:
                    await instance.shutdown()
                except Exception:
                    logger.exception("插件 %s 卸载失败", type(instance).__name__)
            plugin.instances.clear()

        self.plugins.clear()
        clear_command_registry()
        clear_llm_tool_registry()
        clear_active_registry()
