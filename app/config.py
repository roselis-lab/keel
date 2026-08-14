from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the default DB at the project root so it resolves the same way regardless
# of the current working directory. Override with DATABASE_URL for anything else.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "threat_library.db"


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database — SQLite by default for zero-setup local use.
    database_url: str = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.as_posix()}"

    # Read-only REST API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = False

    # MCP
    mcp_server_name: str = "keel"
    mcp_server_version: str = "0.1.0"
    mcp_http_port: int = 8001
    mcp_http_host: str = "127.0.0.1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
