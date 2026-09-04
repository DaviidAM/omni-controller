import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rate_limit import reset_rate_limits


@pytest.fixture(autouse=True)
def _reset():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.mark.asyncio
async def test_demo_rate_limit_enforced():
    """DEMO_RATE_LIMIT is 3 in conftest. 4th request returns 429."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "Authorization": "Bearer test-demo-key-xyz789",
            "X-Forwarded-For": "1.2.3.4",
        }
        # First 3 requests get past auth but may 502 because OmniRoute isn't running.
        # We're testing rate limit, not OmniRoute success.
        statuses = []
        for _ in range(4):
            res = await client.post(
                "/demo/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers=headers,
            )
            statuses.append(res.status_code)
        # First 3 are NOT 429 (they may be 502 because mock OmniRoute is unreachable).
        # 4th must be 429.
        assert statuses[:3] != [429, 429, 429]
        assert statuses[3] == 429


@pytest.mark.asyncio
async def test_agent_rate_limit_enforced():
    """AGENT_RATE_LIMIT is 5 in conftest. 6th request returns 429."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {
            "Authorization": "Bearer test-agent-key-abc123",
            "X-Forwarded-For": "5.6.7.8",
        }
        statuses = []
        for _ in range(6):
            res = await client.post(
                "/agent/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers=headers,
            )
            statuses.append(res.status_code)
        assert statuses[5] == 429


@pytest.mark.asyncio
async def test_rate_limits_per_ip():
    """Different IPs get separate buckets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # IP A fills its bucket
        for _ in range(3):
            await client.post(
                "/demo/chat",
                json={"messages": [{"role": "user", "content": "hi"}]},
                headers={
                    "Authorization": "Bearer test-demo-key-xyz789",
                    "X-Forwarded-For": "10.0.0.1",
                },
            )
        # IP B should still get through auth (may 502)
        res = await client.post(
            "/demo/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            headers={
                "Authorization": "Bearer test-demo-key-xyz789",
                "X-Forwarded-For": "10.0.0.2",
            },
        )
        assert res.status_code != 429
