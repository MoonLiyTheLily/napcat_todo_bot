import json
import logging

from openai.types.chat import (
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
)
from bot.llm.llm_tool_registry import (
    LLMToolContext,
    LLMToolRegistryData,
)
from bot.config.config import config
from bot.llm.client import LLMChatClientOpenAI

logger = logging.getLogger(__name__)


class LLMChatSessionOpenAI:
    """管理单个对话session"""

    def __init__(self, client: LLMChatClientOpenAI, user_id: int) -> None:
        self.user: int = user_id
        self.client: LLMChatClientOpenAI = client
        self.messages_list: list[ChatCompletionMessageParam] = []
        self.tool_context: LLMToolContext = LLMToolContext(self.user)

    @property
    def target_model(self) -> str:
        model = config.get("llm.basic.target_model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("目标模型必须是非空字符串")
        return model

    async def chat(
        self, message: str, tool_list: dict[str, LLMToolRegistryData] | None = None
    ) -> str:
        """发送消息"""
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": "最新消息发送时间" + self.tool_context.user_send_time,
        }
        if not self.messages_list:
            self.messages_list.append(system_message)
        else:
            self.messages_list[0] = system_message
        history_length = len(self.messages_list)
        self.messages_list.append({"role": "user", "content": message})
        try:
            model = self.target_model
            tool_descriptions = (
                [tool_data.description for tool_data in tool_list.values()]
                if tool_list
                else None
            )
            while True:
                response = await self.client.chat_completions(
                    model=model,
                    messages=self.messages_list,
                    tools=tool_descriptions,
                )
                if not response.choices:
                    raise ValueError("模型没有返回任何候选回复")
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                if not tool_calls:
                    content = response_message.content
                    if not content or not content.strip():
                        raise ValueError("模型返回了空回复")
                    content = content.lstrip("\n")
                    self.messages_list.append({"role": "assistant", "content": content})
                    return content

                if not tool_list:
                    raise ValueError("模型请求调用工具，但本次对话未提供工具")
                # 先验证整批工具类型，再写入历史和执行工具。
                tool_calls_data: list[ChatCompletionMessageFunctionToolCallParam] = []
                for tool_call in tool_calls:
                    if tool_call.type != "function":
                        raise ValueError(f"不支持的工具类型：{tool_call.type}")
                    tool_calls_data.append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )
                self.messages_list.append(
                    {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": tool_calls_data,
                    }
                )
                # 每个 tool_call_id 都需要有对应的工具结果。
                for tool_call_data in tool_calls_data:
                    function_name = tool_call_data["function"]["name"]
                    arguments = json.loads(tool_call_data["function"]["arguments"])
                    if not isinstance(arguments, dict):
                        raise ValueError(f"工具 {function_name} 的参数必须是 JSON 对象")
                    logger.info("正在调用工具 [%s]，参数：%s", function_name, arguments)
                    tool_data = tool_list.get(function_name)
                    if tool_data is None:
                        tool_data = tool_list.get("not_found")
                    if tool_data is None or tool_data.function is None:
                        raise ValueError(f"工具 {function_name} 没有可用的处理函数")
                    tool_result = await tool_data.function(self.tool_context, arguments)
                    tool_message: ChatCompletionToolMessageParam = {
                        "role": "tool",
                        "tool_call_id": tool_call_data["id"],
                        "content": tool_result,
                    }
                    logger.info("工具返回：%s", tool_result)
                    self.messages_list.append(tool_message)
        except Exception:
            # 移除本轮失败对话，避免残留不完整的工具调用或用户消息。
            # 已执行工具的外部副作用无法通过删除历史撤销。
            del self.messages_list[history_length:]
            raise

    def clear(self) -> None:
        """重置会话"""
        self.messages_list = [m for m in self.messages_list if m["role"] == "system"]
