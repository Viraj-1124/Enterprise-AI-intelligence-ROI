import httpx

from app.core.enums import PrecisionTier
from app.core.schemas import ModelSpec


class OpenAIAdapter:
    provider = "openai"

    def __init__(self, spec: ModelSpec, api_key: str) -> None:
        self.spec, self.api_key = spec, api_key

    async def health(self) -> bool:
        return True

    async def generate(self, prompt: str, precision: PrecisionTier, **kwargs: object) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.spec.id, "messages": [{"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
