from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Read-only REST API + browse UI
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = False

    # Optional GitHub repo URL (e.g. https://github.com/org/keel). When set, the UI
    # offers an "Edit on GitHub" link on save. Env var: REPO_URL. Empty = link hidden.
    repo_url: str = ""

    # Optional override for the catalog directory (env var: CATALOG_DIR). Point it at a
    # throwaway copy to click through the UI without touching the real catalog. Empty =
    # the repo's own catalog/.
    catalog_dir: str = ""

    # MCP
    mcp_server_name: str = "keel"
    mcp_server_version: str = "0.1.0"
    mcp_http_port: int = 8001
    mcp_http_host: str = "127.0.0.1"

    # extra="ignore" so a stray var in .env (e.g. a leftover DATABASE_URL) never crashes startup.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
