from openai import OpenAI

from app.services.model_provider import ModelProvider, ModelProviderError


class OpenAIProvider(ModelProvider):
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise ModelProviderError(f"OpenAI request failed: {exc}") from exc
        return response.output_text
