import os
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_ROUTING_PATH = Path(__file__).parent / "routing.yaml"


class RoutingConfig:
    def __init__(self, raw: dict):
        self._raw = raw

    @property
    def default_provider(self) -> str:
        return self._raw["default_provider"]

    def provider_config(self, provider: str) -> dict:
        return self._raw["providers"][provider]

    def resolve(self, task_type: str) -> tuple[str, str]:
        """Returns (provider, model) for a task_type, falling back to the
        default provider's default model if the task isn't explicitly routed."""
        route = self._raw["task_routes"].get(task_type)
        if route is not None:
            return route["provider"], route["model"]
        provider = self.default_provider
        model = self.provider_config(provider)["default_model"]
        return provider, model


def _routing_path() -> Path:
    override = os.environ.get("ROUTING_CONFIG_PATH")
    return Path(override) if override else DEFAULT_ROUTING_PATH


@lru_cache
def load_routing_config() -> RoutingConfig:
    path = _routing_path()
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RoutingConfig(raw)
