import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.connectors.providers import ALL_CONNECTORS
from app.config import get_settings
from app.database.session import get_db
from app.models.models import ActivityEvent, Employee, EmployeeConnection
from app.services.auth import get_current_employee

router = APIRouter(prefix="/api/connectors", tags=["connectors"])
settings = get_settings()


@router.get("")
def list_connector_status():
    results = []
    for name, cls in ALL_CONNECTORS.items():
        try:
            status = cls().is_available()
            results.append({"name": name, "available": status.available, "reason": status.reason,
                            "oauth_supported": name == "github" and bool(settings.GITHUB_OAUTH_CLIENT_ID and settings.GITHUB_OAUTH_CLIENT_SECRET)})
        except Exception as exc:  # connector failures must not crash the platform
            results.append({"name": name, "available": False, "reason": f"Connector error: {exc}"})
    return results


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _oauth_state(employee_id: str) -> str:
    payload = {"employee_id": employee_id, "exp": int((datetime.utcnow() + timedelta(minutes=10)).timestamp()), "nonce": secrets.token_urlsafe(18)}
    encoded = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def _read_oauth_state(state: str) -> dict:
    try:
        encoded, signature = state.split(".")
        expected = _b64(hmac.new(settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid OAuth state")
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if payload["exp"] < datetime.utcnow().timestamp():
            raise ValueError("OAuth state expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state") from exc


@router.get("/oauth/{provider}/start")
def start_oauth(provider: str, employee=Depends(get_current_employee)):
    if provider != "github":
        raise HTTPException(status_code=400, detail="OAuth is currently supported for GitHub only")
    if not settings.GITHUB_OAUTH_CLIENT_ID or not settings.GITHUB_OAUTH_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured for this workspace")
    query = urlencode({"client_id": settings.GITHUB_OAUTH_CLIENT_ID, "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                       "scope": "read:user", "state": _oauth_state(employee.id)})
    return {"authorization_url": f"https://github.com/login/oauth/authorize?{query}"}


@router.get("/oauth/github/callback")
def github_oauth_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    payload = _read_oauth_state(state)
    if not settings.GITHUB_OAUTH_CLIENT_ID or not settings.GITHUB_OAUTH_CLIENT_SECRET:
        return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?connection_error=not_configured")
    try:
        with httpx.Client(timeout=15) as client:
            token_response = client.post("https://github.com/login/oauth/access_token", json={
                "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                "state": state,
            }, headers={"Accept": "application/json"})
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise ValueError("GitHub did not return an access token")
            profile = client.get("https://api.github.com/user", headers={
                "Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json",
            })
            profile.raise_for_status()
            account = profile.json()
        connection = db.query(EmployeeConnection).filter(
            EmployeeConnection.employee_id == payload["employee_id"], EmployeeConnection.provider == "github",
        ).first()
        if connection is None:
            connection = EmployeeConnection(employee_id=payload["employee_id"], provider="github")
            db.add(connection)
        connection.account_id = str(account["id"])
        connection.account_name = account.get("login") or account.get("name") or "GitHub account"
        db.add(ActivityEvent(employee_id=payload["employee_id"], event_type="account_connected", source="observed",
                             tool="github", event_metadata={"account": connection.account_name}))
        db.commit()
        # GitHub token is deliberately not persisted. OAuth here links identity only;
        # the platform does not yet sync GitHub repositories or activity.
        del access_token
        return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?connected=github")
    except Exception:
        db.rollback()
        return RedirectResponse(f"{settings.FRONTEND_URL}/connectors?connection_error=oauth_failed")


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    query = db.query(EmployeeConnection)
    if employee.role.value == "employee":
        query = query.filter(EmployeeConnection.employee_id == employee.id)
    rows = query.all()
    names = {employee.id: employee.name for employee in db.query(Employee).filter(
        Employee.id.in_({row.employee_id for row in rows})
    ).all()} if rows else {}
    return [{"id": row.id, "employee_id": row.employee_id, "employee_name": names.get(row.employee_id), "provider": row.provider,
             "account_name": row.account_name, "connected_at": row.connected_at} for row in rows]


@router.delete("/accounts/{provider}")
def disconnect_account(provider: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    query = db.query(EmployeeConnection).filter(EmployeeConnection.provider == provider)
    if employee.role.value == "employee":
        query = query.filter(EmployeeConnection.employee_id == employee.id)
    connection = query.first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connected account not found")
    db.delete(connection)
    db.add(ActivityEvent(employee_id=connection.employee_id, event_type="account_disconnected", source="observed",
                         tool=provider, event_metadata={"account": connection.account_name}))
    db.commit()
    return {"status": "disconnected"}
