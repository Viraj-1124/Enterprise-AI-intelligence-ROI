from fastapi import APIRouter, Depends

from app.api.deps import get_registry
from app.settings import get_settings

router = APIRouter()


@router.get("/v1/models")
async def models(registry=Depends(get_registry)) -> list[dict[str, object]]:  # noqa: B008
    return [m.model_dump(mode="json") for m in registry.list()]


@router.get("/v1/runtime")
async def runtime(registry=Depends(get_registry)) -> dict[str, object]:  # noqa: B008
    settings = get_settings()
    return {
        "model_provider": settings.model_provider.lower(),
        "provider_ready": registry.provider_ready,
        "default_strategy": settings.default_strategy,
        "jev_mode": "http" if settings.jev_base_url else "local_mock",
    }
