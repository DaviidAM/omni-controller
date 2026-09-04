"""Client for OmniRoute."""
import logging
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


def _build_payload(messages: list[dict], model: str | None, temperature: float | None, max_tokens: int | None) -> dict:
    payload: dict[str, Any] = {"messages": messages, "stream": False}
    if model:
        payload["model"] = model
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    return payload


async def chat(
    messages: list[dict],
    combo: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Forward a chat request to OmniRoute with a forced combo.

    Returns the OmniRoute JSON response.
    Raises httpx.HTTPError on transport errors.
    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    if not settings.OMNIROUTE_API_KEY:
        raise RuntimeError("OMNIROUTE_API_KEY not configured")

    payload = _build_payload(messages, model, temperature, max_tokens)
    headers = {
        "Authorization": f"Bearer {settings.OMNIROUTE_API_KEY}",
        # Force OmniRoute to use this combo. The exact header name
        # may need adjustment once we verify with the live OmniRoute.
        "X-Combo-ID": combo,
        "Content-Type": "application/json",
    }

    logger.info(f"Forwarding to OmniRoute: combo={combo}, model={model or 'auto'}")

    async with httpx.AsyncClient(timeout=settings.OMNIROUTE_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.OMNIROUTE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
