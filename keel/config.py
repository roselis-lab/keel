from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Browse UI + REST, as started by `keel up`. Only the port is a setting. The address
    # is not: this API writes files and has no login, so `keel up` binds it to loopback
    # and offers no way to say otherwise. (Env var: UI_PORT.)
    ui_port: int = 8420

    # The names a request may arrive under (env var: ALLOWED_HOSTS, a JSON list).
    # Listening on loopback is half of "local only". The other half is a web page in the
    # user's own browser, which can reach loopback too: it points a name it controls at
    # 127.0.0.1 and then talks to this server as if it were its own. A request that did
    # not ask for one of these names is refused before it reaches a route. Add the public
    # name here when Keel is deliberately served behind one.
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]

    # Optional GitHub repo URL (e.g. https://github.com/org/keel). When set, the UI
    # offers an "Edit on GitHub" link on save. Env var: REPO_URL. Empty = link hidden.
    repo_url: str = ""

    # Hosts an evidence permalink in a report may point to (env var: EVIDENCE_HOSTS, a
    # JSON list, e.g. ["github.com", "git.example.internal"]). An evidence link is model
    # output: a planted address can carry data in its query or lead to a lookalike page.
    # So a link to any other host is refused on save, and the default is no host at all:
    # an organisation names where its code lives. Evidence without a link still works -
    # commit, path, lines and the quote are what it rests on.
    evidence_hosts: list[str] = []

    # Optional override for the catalog directory (env var: CATALOG_DIR). Point it at a
    # throwaway copy to click through the UI without touching the real catalog. Empty =
    # the repo's own catalog/.
    catalog_dir: str = ""

    # Optional override for the reports directory (env var: REPORTS_DIR). Empty = the
    # repo's own reports/, sibling to catalog/.
    reports_dir: str = ""

    # Optional override for the organisation facts directory (env var: ORG_DIR): one
    # YAML file per shared platform or data policy, read by every assessment. Empty =
    # the repo's own org/, sibling to reports/. Private like reports: never committed
    # upstream.
    org_dir: str = ""

    # MCP
    mcp_server_name: str = "keel"
    mcp_server_version: str = "0.1.0"
    mcp_http_port: int = 8001
    mcp_http_host: str = "127.0.0.1"
    # `keel --http` refuses any other address than loopback unless this is set (env var:
    # MCP_HTTP_ALLOW_REMOTE). The HTTP transport exposes the write tools with no login,
    # so reaching it from another machine has to be something someone decided, not
    # something a copied .env did. The container sets it, and publishes the port on the
    # host's loopback only.
    mcp_http_allow_remote: bool = False

    # extra="ignore" so a stray var in .env (e.g. a leftover DATABASE_URL) never crashes startup.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
