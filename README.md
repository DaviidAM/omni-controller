# omni-controller

Multi-endpoint gateway for OmniRoute. Exposes two Bearer-protected paths
that forward chat requests to OmniRoute with different combo configurations.

## Endpoints

| Path | Auth key env var | Rate limit | OmniRoute combo |
|------|------------------|------------|-----------------|
| POST /agent/chat | AGENT_API_KEY | 60 req/min per IP | AGENT_COMBO (default: personal) |
| POST /demo/chat | DEMO_API_KEY | 10 req/min per IP | DEMO_COMBO (default: demo) |

Both endpoints require `Authorization: Bearer *** with the value matching
the env var for that path. The keys must be **different** — the agent key
does NOT authenticate against /demo and vice versa.

## Quick start

```bash
cp .env.example .env
# Fill in real values in .env (DO NOT commit)

docker compose up -d
```

The omni-controller will be available at `http://localhost:8081`. OmniRoute
is exposed internally on `20128` (not published to host).

## Usage

```bash
# Agent endpoint
curl -X POST http://localhost:8081/agent/chat \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# Demo endpoint
curl -X POST http://localhost:8081/demo/chat \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

# Health (no auth required)
curl http://localhost:8081/health
```

## Setup OmniRoute combos

1. Open OmniRoute's web UI (via port 8082 during dev, or via tunnel).
2. Create two combos named exactly as in your env: `personal` (for agent) and `demo` (for demos).
3. Configure each combo with the providers you want (e.g. personal = Groq + Claude + GPT-4o, demo = Gemini Flash only).

The omni-controller will send `X-Combo-ID: personal` for /agent/chat and `X-Combo-ID: demo` for /demo/chat. OmniRoute is expected to honor that header (verify in OmniRoute's docs).

## Exposing publicly (cloudflared tunnel)

```bash
cloudflared tunnel --url http://localhost:8081
```

Use the resulting `*.trycloudflare.com` URL as the public endpoint.

## Running tests

```bash
cd backend
uv pip install -r requirements.txt
pytest -v
```

Tests mock OmniRoute — no running OmniRoute needed.
