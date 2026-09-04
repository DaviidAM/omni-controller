"""Settings loaded from environment variables at startup."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Auth — different keys for each path
    AGENT_API_KEY: str = ""
    DEMO_API_KEY: str = ""

    # OmniRoute
    OMNIROUTE_URL: str = "http://omniroute:20128"
    OMNIROUTE_API_KEY: str = ""
    OMNIROUTE_TIMEOUT_SECONDS: float = 30.0

    # Combo IDs that exist in OmniRoute (Daviid creates these in OmniRoute web UI)
    AGENT_COMBO: str = "personal"
    DEMO_COMBO: str = "demo"

    # Rate limits (per minute per IP)
    AGENT_RATE_LIMIT: int = 60
    DEMO_RATE_LIMIT: int = 10

    # Server
    PUBLIC_PORT: int = 8081


settings = Settings()
