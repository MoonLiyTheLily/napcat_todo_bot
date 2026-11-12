from collections.abc import Iterable, Sequence

from openai import AsyncOpenAI, omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from bot.config.config import config


class LLMChatClientOpenAI:
    """管理单个OpenAI Client"""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._cached_api_key: str | None = None
        self._cached_base_url: str | None = None

    @property
    def client(self) -> AsyncOpenAI:
        api_key = config.get("llm.basic.api_key")
        base_url = config.get("llm.basic.base_url")
        if (
            self._client is None
            or self._cached_api_key != api_key
            or self._cached_base_url != base_url
        ):
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self._cached_api_key = api_key
            self._cached_base_url = base_url
        return self._client

    async def chat_completions(
        self,
        model: str,
        messages: Sequence[ChatCompletionMessageParam],
        *,
        tools: Iterable[ChatCompletionToolUnionParam] | None = None,
    ) -> ChatCompletion:
        """发送非流式对话请求，未提供工具时省略 tools 参数。"""
        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools is not None else omit,
            stream=False,
        )
