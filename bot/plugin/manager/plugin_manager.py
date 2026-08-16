import os
import logging
from pathlib import Path
import importlib
from types import ModuleType
from typing import Any
import pydantic
from bot.plugin.basic_plugin import BasicPlugin
from bot.plugin.manager.plugin_registry import (
    clear_command_registry,
    auto_register,
)
from bot.llm.llm_tool_registry import clear_llm_tool_registry
from bot.active.active_registry import clear_active_registry

logger = logging.getLogger(__name__)


def get_bot_root():
    return os.path.realpath(os.getcwd())


def get_builtin_plugin_path():
    return os.path.realpath(os.path.join(get_bot_root(), "bot", "plugin", "builtin"))


def get_other_plugin_path():
    return os.path.realpath(os.path.join(get_bot_root(), "bot", "plugin", "other"))


def get_config_path():
    return os.path.realpath(os.path.join(get_bot_root(), "config"))


class PluginData(pydantic.BaseModel):
    name: str
    file_path: Path
    module_path: str
    builtin: bool


class PluginManager:
    _instances: list["PluginManager"] = []

    def __init__(self) -> None:
        self.__class__._instances.append(self)
        self.plugin_list: list[PluginData] = []
        self.module_list: list[tuple[str, ModuleType]] = []
        self.plugin_instances: list[BasicPlugin] = []
        self.plugin_context: Any = None

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
        builtin_list = self._get_module_file(get_builtin_plugin_path())
        other_list = []
        if os.path.exists(get_other_plugin_path()):
            other_list = self._get_module_file(get_other_plugin_path())
        return {
            "builtin": builtin_list,
            "other": other_list,
        }

    async def load(self) -> None:
        """加载插件（异步初始化）"""

        self.plugin_list.clear()
        self.module_list.clear()
        self.plugin_instances.clear()

        plugin_module_list = self._get_plugin_modules()
        for plugin in plugin_module_list["builtin"]:
            import_module_path = (
                "bot.plugin.builtin." + plugin["name"] + "." + plugin["module_name"]
            )
            m = importlib.import_module(import_module_path)
            self.plugin_list.append(
                PluginData(
                    name=plugin["name"],
                    file_path=Path(plugin["path"]),
                    module_path=import_module_path,
                    builtin=True,
                )
            )
            self.module_list.append((plugin["name"], m))
        for plugin in plugin_module_list["other"]:
            import_module_path = (
                "bot.plugin.other." + plugin["name"] + "." + plugin["module_name"]
            )
            m = importlib.import_module(import_module_path)
            self.plugin_list.append(
                PluginData(
                    name=plugin["name"],
                    file_path=Path(plugin["path"]),
                    module_path=import_module_path,
                    builtin=False,
                )
            )
            self.module_list.append((plugin["name"], m))
        self.plugin_instances = auto_register()

        for instance in self.plugin_instances:
            try:
                await instance.initialize()
            except Exception:
                logger.exception("插件 %s 异步初始化失败", type(instance).__name__)

    async def reload(self) -> None:
        """清除注册表，重载插件模块，重新注册"""

        clear_command_registry()
        clear_llm_tool_registry()
        clear_active_registry()

        try:
            for _, module in self.module_list:
                importlib.reload(module)
        except ModuleNotFoundError as e:
            logger.exception("重载错误: %s", e)

        await self.load()
