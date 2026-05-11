import os
import copy
import json
import logging
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """应用配置管理器

    配置加载优先级：
    1. config.json 作为基础配置
    2. .env 中的密钥字段（api_key, base_url, admin_user_id）覆盖 json 中的值
    3. 运行时通过 set() 修改的值写入内存，可通过 save() 持久化到 json
    """

    CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"

    # .env 中需要覆盖到配置的密钥字段映射
    # key: .env 中的变量名, value: 配置中的点分路径
    ENV_OVERRIDES = {
        "api_key": "llm.basic.api_key",
        "base_url": "llm.basic.base_url",
        "admin_user_id": "admin_user_id",
    }

    def __init__(self) -> None:
        load_dotenv(Path(__file__).parent.parent.parent / ".env")
        self._data: dict[str, Any] = self._load()
        self._defaults: dict[str, Any] = copy.deepcopy(self._data)

    def _load(self) -> dict[str, Any]:
        """从 config.json 加载配置，再用 .env 密钥覆盖"""
        if not self.CONFIG_PATH.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.CONFIG_PATH}")
        with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # .env 密钥覆盖
        for env_key, config_path in self.ENV_OVERRIDES.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                self._set_nested(data, config_path, env_value)

        # admin_user_id 转为 int
        raw_admin = self._get_nested(data, "admin_user_id")
        if isinstance(raw_admin, str):
            self._set_nested(data, "admin_user_id", int(raw_admin))

        return data

    @staticmethod
    def _get_nested(data: dict[str, Any], path: str) -> Any:
        """点分路径访问嵌套 dict"""
        keys = path.split(".")
        value = data
        for key in keys:
            value = value[key]
        return value

    @staticmethod
    def _set_nested(data: dict[str, Any], path: str, value: Any) -> None:
        """点分路径设置嵌套 dict 值"""
        keys = path.split(".")
        target = data
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value

    def get(self, path: str) -> Any:
        """点分路径访问配置，如 config.get("llm.basic.api_key")"""
        return self._get_nested(self._data, path)

    def set(self, path: str, value: Any) -> None:
        """点分路径修改配置，带类型校验，保持与原值类型一致"""
        old = self.get(path)
        if isinstance(old, bool):
            if isinstance(value, str):
                value = value == "True"
            target_value = value
        elif isinstance(old, int):
            target_value = int(value)
        elif isinstance(old, str):
            target_value = str(value)
        else:
            target_value = value
        self._set_nested(self._data, path, target_value)
        logger.info("配置项 %s 已更改为 %s", path, target_value)

    def reset(self) -> None:
        """恢复所有配置到默认值（json + .env 的初始状态）"""
        self._data = copy.deepcopy(self._defaults)

    def save(self) -> None:
        """将当前配置持久化到 config.json"""
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)
        logger.info("配置已保存到 %s", self.CONFIG_PATH)

    def to_dict(self) -> dict:
        """返回完整配置的深拷贝"""
        return copy.deepcopy(self._data)