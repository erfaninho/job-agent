import json
from abc import ABC, abstractmethod
from typing import Any

from app.config import Settings, get_settings


class ModelProviderError(RuntimeError):
    pass


class ModelProvider(ABC):
    @abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        text = self.generate_text(
            system_prompt,
            f"{user_prompt}\n\nReturn JSON matching this schema:\n{json.dumps(schema)}",
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelProviderError("Model did not return valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ModelProviderError("Model JSON response was not an object.")
        return parsed


class LocalRulesProvider(ModelProvider):
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return f"{system_prompt.strip()}\n\n{user_prompt.strip()}".strip()

    def generate_json(
        self, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            parsed = json.loads(user_prompt)
        except json.JSONDecodeError as exc:
            raise ModelProviderError("Local JSON input was not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ModelProviderError("Local JSON input was not an object.")
        return parsed


def get_model_provider(settings: Settings | None = None) -> ModelProvider:
    resolved = settings or get_settings()
    provider = resolved.model_provider.lower()
    if provider == "ollama":
        from app.services.providers.ollama_provider import OllamaProvider

        return OllamaProvider(resolved.ollama_base_url, resolved.ollama_model)
    if provider == "openai":
        if not resolved.openai_api_key:
            raise ModelProviderError("OPENAI_API_KEY is required when MODEL_PROVIDER=openai.")
        from app.services.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(resolved.openai_api_key, resolved.openai_model)
    if provider == "lmstudio":
        if not resolved.lmstudio_model:
            raise ModelProviderError("LMSTUDIO_MODEL is required when MODEL_PROVIDER=lmstudio.")
        from app.services.providers.lmstudio_provider import LMStudioProvider

        return LMStudioProvider(resolved.lmstudio_base_url, resolved.lmstudio_model)
    if provider in {"local", "local-rules"}:
        return LocalRulesProvider()
    raise ModelProviderError(f"Unsupported MODEL_PROVIDER: {resolved.model_provider}")
