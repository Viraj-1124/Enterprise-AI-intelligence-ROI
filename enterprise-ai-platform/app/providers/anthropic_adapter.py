import httpx

from app.core.enums import PrecisionTier
from app.core.schemas import ModelSpec


class AnthropicAdapter:
    provider = "anthropic"

    def __init__(self, spec: ModelSpec, api_key: str) -> None:
        self.spec, self.api_key = spec, api_key

    async def health(self) -> bool:
        return True

    async def generate(self, prompt: str, precision: PrecisionTier, **kwargs: object) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": self.spec.id,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
