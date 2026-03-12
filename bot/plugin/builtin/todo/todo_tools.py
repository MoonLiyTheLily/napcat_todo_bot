descriptions = {
    "create_todo": {
        "type": "function",
        "function": {
            "name": "create_todo",
            "description": "创建一个待办",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "待办的标题，要求简单明了",
                    },
                    "date": {
                        "type": ["string", "null"],
                        "description": "这个参数不是必须的。如果用户明确指出某个时间，请*先获取用户当前时间*，再总结日期，格式'YYYY-MM-DD HH:MM:SS'，例如'2026-02-01 12:00:00'，对于用户没有确切指定的分、秒，应当设置为整点、整分，也就是00分00秒，如果没有指定小时，应当设置为当天的早上8点",
                    },
                },
                "required": ["content"],
            },
        },
    },
    "check_todo": {
        "type": "function",
        "function": {
            "name": "check_todo",
            "description": "检查用户现有的待办，待办可能带有图标，如果是✅，说明这个待办完成了，如果是❎，说明这个待办没有完成",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    "delete_todo": {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "删除一个，或者所有待办",
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id_or_all": {
                        "type": "string",
                        "description": "通过check_todo得到的待办列表里的次序。例如：如果你希望删除前面几条，需要重复执行“删除第一个代办”",
                    },
                },
                "required": ["todo_id_or_all"],
            },
        },
    },
    "get_current_time": {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取用户当前的时间",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
}
