from openai import OpenAI

from app.services.model_provider import ModelProvider, ModelProviderError


class LMStudioProvider(ModelProvider):
    def __init__(self, base_url: str, model: str):
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")
        self.model = model

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            raise ModelProviderError(f"LM Studio request failed: {exc}") from exc
        return response.choices[0].message.content or ""
