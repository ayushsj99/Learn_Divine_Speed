import json
import logging
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from lgs_shared.models.llm import LLMRequest, LLMResponse

from llm_router.config_loader import load_routing_config
from llm_router.providers.base import BaseProvider
from llm_router.providers.ollama_provider import OllamaProvider
from llm_router.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("llm_router")
app = FastAPI(title="LLM Router Service")


@lru_cache
def _providers() -> dict[str, BaseProvider]:
    cfg = load_routing_config()
    providers: dict[str, BaseProvider] = {}
    ollama_cfg = cfg.provider_config("ollama")
    providers["ollama"] = OllamaProvider(
        base_url_env=ollama_cfg["base_url_env"], base_url_default=ollama_cfg["base_url_default"]
    )
    openai_cfg = cfg.provider_config("openai")
    try:
        providers["openai"] = OpenAIProvider(api_key_env=openai_cfg["api_key_env"])
    except RuntimeError as exc:
        logger.warning("OpenAI provider unavailable: %s", exc)
    return providers


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/generate", response_model=LLMResponse)
async def generate(req: LLMRequest) -> LLMResponse:
    cfg = load_routing_config()
    provider_name, model = cfg.resolve(req.task_type.value)
    providers = _providers()

    provider = providers.get(provider_name)
    if provider is None:
        raise HTTPException(
            status_code=503, detail=f"Provider '{provider_name}' is not configured"
        )

    prompt = req.payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="payload.prompt is required")

    try:
        raw = await provider.generate(model=model, prompt=prompt, response_format=req.response_format)
    except Exception as exc:
        logger.exception("Provider '%s' failed for task_type=%s", provider_name, req.task_type)
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}") from exc

    if req.response_format == "json":
        try:
            return LLMResponse(json_data=json.loads(raw), provider=provider_name, model=model)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502, detail=f"Provider returned invalid JSON: {exc}"
            ) from exc

    return LLMResponse(text=raw, provider=provider_name, model=model)
