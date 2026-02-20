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
}
