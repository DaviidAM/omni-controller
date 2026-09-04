import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
def _reset_limits():
    from app.rate_limit import reset_rate_limits
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.mark.asyncio
async def test_health_does_not_require_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_agent_requires_bearer_header():
    """Missing Authorization header → 401 (our auth dependency explicitly checks for it)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_agent_rejects_missing_authorization():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer"},  # no token
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_agent_rejects_wrong_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_agent_rejects_demo_key():
    """The DEMO_API_KEY must NOT authenticate against /agent/*."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer test-demo-key-xyz789"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_demo_rejects_agent_key():
    """The AGENT_API_KEY must NOT authenticate against /demo/*."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/demo/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer test-agent-key-abc123"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_demo_rejects_wrong_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/demo/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_agent_rejects_non_bearer_authorization():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/agent/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert res.status_code == 401
