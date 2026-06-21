import httpx

from app.services.model_provider import ModelProvider, ModelProviderError


class OllamaProvider(ModelProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelProviderError(f"Ollama request failed: {exc}") from exc
        data = response.json()
        return str(data.get("message", {}).get("content", ""))

    def check_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except httpx.HTTPError:
            return False
