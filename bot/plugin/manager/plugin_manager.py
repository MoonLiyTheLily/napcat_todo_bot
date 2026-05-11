import os
import logging
from pathlib import Path
import importlib
from types import ModuleType
import pydantic
from bot.plugin.manager.plugin_registry import (
    clear_command_registry,
    auto_register,
)
from bot.llm.llm_tool_registry import clear_llm_tool_registry

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

    @staticmethod
    def _get_module_file(path: str) -> list[dict[str, str]]:        modules = []
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
        other_list = self._get_module_file(get_other_plugin_path())
        return {
            "builtin": builtin_list,
            "other": other_list,
        }

    def load(self) -> None:
        """加载插件"""

        self.plugin_list.clear()
        self.module_list.clear()

        plugin_module_list = self._get_plugin_modules()
        for plugin in plugin_module_list["builtin"]:
            import_module_path = (
                "bot.plugin.builtin." + plugin["name"] + "." + plugin["module_name"]
            )
            m = importlib.import_module(import_module_path)
            self.plugin_list.append(
                PluginData(
                    name=plugin["name"],
                    file_path=plugin["path"],
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
                    file_path=plugin["path"],
                    module_path=import_module_path,
                    builtin=False,
                )
            )
            self.module_list.append((plugin["name"], m))
        auto_register()

    def reload(self) -> None:
        """清除命令注册表，然后重载插件"""

        clear_llm_tool_registry()
        clear_command_registry()
        try:
            for _, module in self.module_list:
                importlib.reload(module)
        except ModuleNotFoundError as e:
            logger.exception("重载错误: %s", e)
        self.load()
