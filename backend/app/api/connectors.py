from fastapi import APIRouter

from app.connectors.providers import ALL_CONNECTORS

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


@router.get("")
def list_connector_status():
    results = []
    for name, cls in ALL_CONNECTORS.items():
        try:
            status = cls().is_available()
            results.append({"name": name, "available": status.available, "reason": status.reason})
        except Exception as exc:  # connector failures must not crash the platform
            results.append({"name": name, "available": False, "reason": f"Connector error: {exc}"})
    return results
