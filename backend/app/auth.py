"""Bearer token validation as FastAPI dependencies."""
from fastapi import Header, HTTPException, status

from .config import settings


def _check_bearer(authorization: str | None, expected_key: str, key_name: str) -> str:
    """Validate Bearer token against expected key. Returns the token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[len("Bearer "):].strip()
    if not expected_key:
        # Server misconfiguration — don't reveal which key is missing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{key_name} not configured on server",
        )
    if token != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid {key_name}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def require_agent_key(authorization: str | None = Header(default=None)) -> str:
    """Validate Bearer token matches AGENT_API_KEY."""
    return _check_bearer(authorization, settings.AGENT_API_KEY, "AGENT_API_KEY")


def require_demo_key(authorization: str | None = Header(default=None)) -> str:
    """Validate Bearer token matches DEMO_API_KEY."""
    return _check_bearer(authorization, settings.DEMO_API_KEY, "DEMO_API_KEY")
