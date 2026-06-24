import os
from typing import Literal

from openai import AsyncOpenAI

from llm_router.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key_env: str):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing required environment variable: {api_key_env}")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self, model: str, prompt: str, response_format: Literal["text", "json"]
    ) -> str:
        kwargs: dict = {}
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        resp = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return resp.choices[0].message.content or ""
