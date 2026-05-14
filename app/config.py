import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(override=True)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _bool_env(name: str, default: bool) -> bool:
    value = _optional_env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = _optional_env("OPENAI_API_KEY")
    openai_base_url: str | None = _optional_env("OPENAI_BASE_URL")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    python_version: str = os.getenv("PYTHON_VERSION", "3.11")
    llm_timeout_seconds: float = 20.0
    llm_max_retries: int = 2
    llm_store_responses: bool = _bool_env("OPENAI_STORE_RESPONSES", True)

    def __post_init__(self) -> None:
        if self.openai_api_key is not None:
            object.__setattr__(self, "openai_api_key", self.openai_api_key.strip() or None)
        if self.openai_base_url is not None:
            object.__setattr__(self, "openai_base_url", self.openai_base_url.strip() or None)
        object.__setattr__(self, "model_name", self.model_name.strip() or "gpt-4o-mini")


settings = Settings()
