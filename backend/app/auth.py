from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings

admin_token_header = APIKeyHeader(name="X-Admin-Token", auto_error=False)


def verify_admin_token(token: str = Security(admin_token_header)) -> str:
    if not token or token != settings.ADMIN_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return token


def ensure_token_configured():
    if not settings.ADMIN_API_TOKEN:
        raise RuntimeError("ADMIN_API_TOKEN is not configured. Set it in .env before starting the server.")
