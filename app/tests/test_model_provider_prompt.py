from pathlib import Path
from typing import Any, cast

import pytest

from app.config import Settings
from app.services.providers.ollama_provider import OllamaProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.model_provider import LocalRulesProvider, ModelProviderError, get_model_provider
from app.services.prompt_loader import PromptLoader


def test_model_provider_factory_local() -> None:
    settings = Settings(MODEL_PROVIDER="local")
    provider = get_model_provider(settings)
    assert isinstance(provider, LocalRulesProvider)


def test_model_provider_factory_openai_requires_key() -> None:
    settings = Settings(MODEL_PROVIDER="openai", OPENAI_API_KEY="")
    with pytest.raises(ModelProviderError):
        get_model_provider(settings)


def test_prompt_loader(tmp_path: Path) -> None:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    prompt = prompt_dir / "example.md"
    prompt.write_text("Prompt body", encoding="utf-8")
    loader = PromptLoader(prompt_dir)
    assert loader.load("example.md") == "Prompt body"
    assert loader.version("example.md").startswith("example.md:")


def test_local_provider_json_generation() -> None:
    provider = LocalRulesProvider()
    assert provider.generate_json("", '{"ok": true}', {"type": "object"}) == {"ok": True}


def test_ollama_connection_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        status_code = 200

    def fake_get(url: str, timeout: int) -> Response:
        assert url == "http://localhost:11434/api/tags"
        assert timeout == 5
        return Response()

    monkeypatch.setattr("httpx.get", fake_get)
    assert OllamaProvider("http://localhost:11434", "qwen2.5-coder:3b").check_available()


def test_openai_provider_mocked_api() -> None:
    class Responses:
        def create(self, **kwargs: object) -> object:
            assert kwargs["model"] == "test-model"

            class Response:
                output_text = "ok"

            return Response()

    class Client:
        responses = Responses()

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = cast(Any, Client())
    provider.model = "test-model"
    assert provider.generate_text("system", "user") == "ok"
