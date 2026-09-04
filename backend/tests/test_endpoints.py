"""Tests that the endpoints correctly forward to OmniRoute.

OmniRoute itself isn't running during tests. We mock the omniroute.chat
function directly to verify the endpoints handle responses correctly.
"""
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rate_limit import reset_rate_limits


@pytest.fixture(autouse=True)
def _reset():
    reset_rate_limits()
    yield
    reset_rate_limits()


def _mock_omniroute_response(content: str = "Hello back", model: str = "gpt-4o-mini") -> dict:
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@pytest.mark.asyncio
async def test_agent_forwards_with_agent_combo():
    """POST /agent/chat with correct key returns OmniRoute response with agent combo."""
    response = _mock_omniroute_response(content="agent reply")
    mock_chat = AsyncMock(return_value=response)

    # Patch where it's used (main.py imports it as omniroute_chat)
    with patch("app.main.omniroute_chat", mock_chat):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/agent/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-agent-key-abc123",
                    "X-Forwarded-For": "1.1.1.1",
                },
            )

    assert res.status_code == 200
    data = res.json()
    assert data["content"] == "agent reply"
    assert data["combo"] == "personal"
    mock_chat.assert_awaited_once()
    _, call_kwargs = mock_chat.call_args
    assert call_kwargs["combo"] == "personal"


@pytest.mark.asyncio
async def test_demo_forwards_with_demo_combo():
    """POST /demo/chat with correct key returns OmniRoute response with demo combo."""
    response = _mock_omniroute_response(content="demo reply")
    mock_chat = AsyncMock(return_value=response)

    with patch("app.main.omniroute_chat", mock_chat):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/demo/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-demo-key-xyz789",
                    "X-Forwarded-For": "2.2.2.2",
                },
            )

    assert res.status_code == 200
    data = res.json()
    assert data["content"] == "demo reply"
    assert data["combo"] == "demo"
    mock_chat.assert_awaited_once()
    _, call_kwargs = mock_chat.call_args
    assert call_kwargs["combo"] == "demo"


@pytest.mark.asyncio
async def test_agent_sends_combo_header():
    """Verify that /agent/chat calls omniroute_chat with combo='personal'."""
    response = _mock_omniroute_response()
    mock_chat = AsyncMock(return_value=response)

    with patch("app.main.omniroute_chat", mock_chat):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/agent/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-agent-key-abc123",
                    "X-Forwarded-For": "3.3.3.3",
                },
            )

    mock_chat.assert_awaited_once()
    _, call_kwargs = mock_chat.call_args
    assert call_kwargs["combo"] == "personal"


@pytest.mark.asyncio
async def test_demo_sends_combo_header():
    """Verify that /demo/chat calls omniroute_chat with combo='demo'."""
    response = _mock_omniroute_response()
    mock_chat = AsyncMock(return_value=response)

    with patch("app.main.omniroute_chat", mock_chat):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/demo/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-demo-key-xyz789",
                    "X-Forwarded-For": "4.4.4.4",
                },
            )

    mock_chat.assert_awaited_once()
    _, call_kwargs = mock_chat.call_args
    assert call_kwargs["combo"] == "demo"


@pytest.mark.asyncio
async def test_agent_returns_502_on_omniroute_error():
    """When omniroute.chat raises, /agent/chat returns 502."""
    async def fake_chat(*args, **kwargs):
        raise ConnectionError("refused")

    with patch("app.main.omniroute_chat", fake_chat):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/agent/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-agent-key-abc123",
                    "X-Forwarded-For": "5.5.5.5",
                },
            )

    assert res.status_code == 502


@pytest.mark.asyncio
async def test_validation_empty_messages():
    """Sending empty messages array returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": []},
            headers={
                "Authorization": "Bearer test-agent-key-abc123",
                "X-Forwarded-For": "6.6.6.6",
            },
        )
    assert res.status_code == 422
