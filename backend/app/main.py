"""omni-controller — FastAPI gateway for OmniRoute with 2 protected endpoints."""
import logging

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import require_agent_key, require_demo_key
from .config import settings
from .models import ChatRequest, ChatResponse, HealthResponse, Message
from .omniroute import chat as omniroute_chat
from .rate_limit import check_rate_limit, get_client_ip

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


app = FastAPI(
    title="omni-controller",
    version="0.1.0",
    description="Multi-endpoint gateway for OmniRoute",
)


# CORS — wide open because both endpoints require Bearer auth.
# The auth check is the real security boundary.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="omni-controller",
        omni_configured=bool(settings.OMNIROUTE_API_KEY),
    )


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(
    request: Request,
    body: ChatRequest,
    _token: str = Depends(require_agent_key),
) -> ChatResponse:
    """Private endpoint for Daviid's personal agent. Rate limit per IP."""
    ip = get_client_ip(request)
    check_rate_limit(f"agent:{ip}", settings.AGENT_RATE_LIMIT, window_seconds=60)

    try:
        result = await omniroute_chat(
            messages=[m.model_dump() for m in body.messages],
            combo=settings.AGENT_COMBO,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except Exception as exc:
        logger.exception(f"agent_chat failed (combo={settings.AGENT_COMBO})")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream error")

    return _to_response(result, settings.AGENT_COMBO)


@app.post("/demo/chat", response_model=ChatResponse)
async def demo_chat(
    request: Request,
    body: ChatRequest,
    _token: str = Depends(require_demo_key),
) -> ChatResponse:
    """Public endpoint for demos. Rate limit per IP (stricter)."""
    ip = get_client_ip(request)
    check_rate_limit(f"demo:{ip}", settings.DEMO_RATE_LIMIT, window_seconds=60)

    try:
        result = await omniroute_chat(
            messages=[m.model_dump() for m in body.messages],
            combo=settings.DEMO_COMBO,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except Exception as exc:
        logger.exception(f"demo_chat failed (combo={settings.DEMO_COMBO})")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream error")

    return _to_response(result, settings.DEMO_COMBO)


def _to_response(omniroute_result: dict, combo: str) -> ChatResponse:
    """Extract the standard fields from OmniRoute's OpenAI-shaped response."""
    try:
        content = omniroute_result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.error(f"Unexpected OmniRoute response shape: {omniroute_result}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Bad upstream response")

    return ChatResponse(
        content=content,
        model=omniroute_result.get("model"),
        usage=omniroute_result.get("usage"),
        combo=combo,
    )
