import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
api_key = os.getenv("api_key")
base_url = os.getenv("base_url")
target_model = os.getenv("target_model")


DEFAULT_CONFIG = {
    "websocket_host": "127.0.0.1",
    "websocket_port": 8000,
    "active": {
        "todo": {
            "notify_interval": 1800,  # 单位秒
        },
        "gravity": {
            "check_interval": 3600,  # 单位秒
            "threshold": 60,  # 单位分钟
            "earliest": 1440,  # 单位分钟
        },
    },
    "llm": {
        "enabled": True,
        "basic": {
            "api_key": api_key,
            "base_url": base_url,
            "target_model": target_model,
        },
    },
}
