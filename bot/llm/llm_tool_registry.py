from typing import Callable


class LLMToolRegistryData:
    def __init__(self, name, description, function: Callable | None = None) -> None:
        self.name: str = name
        self.description: dict = description
        self.function: Callable | None = function


class LLMToolContext:
    def __init__(
        self,
        user_id: int,
    ) -> None:
        self.user_id = user_id
        self.user_send_time: str = ""


not_found_description = {
    "type": "function",
    "function": {
        "name": "not_found",
        "description": "这是你不应该调用的函数",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}


async def not_found(tool_context, arguments):
    print("LLM调用了不存在的函数")
    return "调用了不存在的命令。"


not_found_data = LLMToolRegistryData("not_found", not_found_description, not_found)


llm_tool_registry: dict[str, LLMToolRegistryData] = {"not_found": not_found_data}


def register_llm_tool(command: str, description):
    llm_tool_registry.update({command: LLMToolRegistryData(command, description)})

    def decorator(func):
        func.__llm_tool_name__ = command
        return func

    return decorator


def clear_llm_tool_registry():
    llm_tool_registry.clear()
    llm_tool_registry.update({"not_found": not_found_data})
