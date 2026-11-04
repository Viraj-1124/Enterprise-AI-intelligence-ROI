import httpx

from app.core.enums import PrecisionTier
from app.core.errors import OllamaUnreachable
from app.core.schemas import ModelSpec


class OllamaAdapter:
    provider = "ollama"

    def __init__(
        self,
        spec: ModelSpec,
        base_url: str = "http://localhost:11434",
        provider_ready: bool = True,
    ) -> None:
        self.spec, self.base_url = spec, base_url.rstrip("/")
        self.provider_ready = provider_ready

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                expected = self.spec.id
                return any(
                    model.get("name") == expected or model.get("model") == expected
                    for model in models
                )
        except (httpx.HTTPError, ValueError):
            return False

    async def preflight(self) -> bool:
        self.provider_ready = await self.health()
        return self.provider_ready

    async def generate(self, prompt: str, precision: PrecisionTier, **kwargs: object) -> str:
        if not self.provider_ready:
            raise OllamaUnreachable(
                f"Ollama model {self.spec.id!r} did not pass startup health check"
            )
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.spec.id, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json()["response"]
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise OllamaUnreachable(
                f"Ollama request failed for {self.spec.id!r}: {error}"
            ) from error
