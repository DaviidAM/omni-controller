# Architecture

## Flow

```
Client (browser/server)
        |
        |  POST /agent/chat  (or /demo/chat)
        |  Authorization: Bearer ***
        v
+-------------------------+
| omni-controller :8081   |
|  - Auth check           |
|  - Rate limit per IP    |
|  - Inject X-Combo-ID    |
+-------------------------+
        |
        |  POST /v1/chat/completions
        |  X-Combo-ID: personal  (or demo)
        |  Bearer: <OMNIROUTE_API_KEY>
        v
+-------------------------+
| OmniRoute :20128        |
|  - Select combo by HDR  |
|  - Pick provider        |
|  - Forward to LLM       |
+-------------------------+
        |
        v
   LLM Provider
```

## Files of interest

- `backend/app/main.py` — FastAPI app and the 2 endpoints
- `backend/app/auth.py` — Bearer token validation
- `backend/app/rate_limit.py` — Sliding window limiter (in-memory)
- `backend/app/omniroute.py` — httpx client that injects X-Combo-ID
- `backend/app/config.py` — Pydantic settings (all from env)

## Security model

- Both endpoints require Bearer auth. No endpoint is unauthenticated.
- Rate limit per source IP (not per token, because tokens may be embedded in clients).
- CORS is wide open (`allow_origins=["*"]`) because the auth header is the real boundary.
- 502 errors return generic message to clients, full traceback in logs only.
- In-memory rate limit resets on restart (acceptable for small scale).
