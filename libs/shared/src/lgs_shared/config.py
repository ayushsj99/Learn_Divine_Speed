import os


def env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value  # type: ignore[return-value]


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw is not None else default
