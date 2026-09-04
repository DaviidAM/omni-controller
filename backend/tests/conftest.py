"""Shared test fixtures."""
import os

# Set required env vars BEFORE any app import so Pydantic settings load correctly.
os.environ.setdefault("AGENT_API_KEY", "test-agent-key-abc123")
os.environ.setdefault("DEMO_API_KEY", "test-demo-key-xyz789")
os.environ.setdefault("OMNIROUTE_API_KEY", "test-omniroute-key")
os.environ.setdefault("OMNIROUTE_URL", "http://mock-omniroute:20128")
os.environ.setdefault("AGENT_COMBO", "personal")
os.environ.setdefault("DEMO_COMBO", "demo")
os.environ.setdefault("AGENT_RATE_LIMIT", "5")
os.environ.setdefault("DEMO_RATE_LIMIT", "3")
