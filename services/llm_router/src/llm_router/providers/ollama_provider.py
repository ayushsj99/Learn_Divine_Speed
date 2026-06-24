import os
from typing import Literal

import httpx

from llm_router.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, base_url_env: str, base_url_default: str):
        self.base_url = os.environ.get(base_url_env, base_url_default)

    async def generate(
        self, model: str, prompt: str, response_format: Literal["text", "json"]
    ) -> str:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if response_format == "json":
            payload["format"] = "json"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()["response"]
