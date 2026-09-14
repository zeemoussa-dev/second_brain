import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The settings a fresh install genuinely cannot run without, in the order the
# setup wizard asks for them (REQ-SB-89). Every one of these used to be a
# REQUIRED pydantic field, which made `Settings()` below raise a
# ValidationError at MODULE IMPORT on a fresh install -- FastAPI never
# started, so no route was ever mounted and no UI could ever fix the very
# config that broke it. They are all optional-with-empty-defaults now, and
# "is it actually configured?" is asked explicitly via `setup_required`
# instead of implicitly by whether an import blew up. Same route the
# 2026-09-03 `fix(config)` commit already took for the Anthropic pair and
# `hermes_mcp_shared_secret`.
REQUIRED_FOR_STARTUP: tuple[str, ...] = (
    "vault_path",
    "self_email",
    "compass_base_url",
    "compass_api_key",
    "compass_model",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    compass_base_url: str = ""
    compass_api_key: str = ""
    compass_model: str = ""
    # Semantic search (REQ-SB-06) reuses the SAME Compass subscription and key
    # as chat -- a separate provider would mean a second credential to keep
    # alive for no gain. Only the model and the route differ, so these three
    # are all that is needed on top of the trio above.
    compass_embedding_model: str = "text-embedding-3-large"
    # `dimensions` is sent only when > 0: the parameter is a Matryoshka-style
    # truncation supported by text-embedding-3-*, and an older deployment
    # (ada-002) rejects the request outright rather than ignoring it. 1024
    # keeps the whole store ~8MB at this vault's scale with no measurable
    # recall loss versus the native 3072.
    compass_embedding_dimensions: int = 1024
    # Override only when the embeddings route does not sit beside the chat
    # route on the same host; otherwise it is derived (see the property
    # below), so a normal install configures nothing here.
    compass_embeddings_url: str = ""
    # Optional since 2026-09-03. Nothing calls Anthropic any more: the
    # `anthropic` SDK is no longer imported anywhere in `app/`, and agent chat
    # moved to Hermes in the 2026-08-20 pivot. The only remaining readers are
    # `data_access/providers.py`, which seeds a Provider row for display -- an
    # empty credential simply shows as unconfigured, which is accurate.
    # Requiring them only stopped a fresh install from booting.
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    # `None` (not a placeholder Path) is deliberate: there is no Path value
    # that honestly means "unset" -- Path("") silently resolves to the CWD,
    # which would point the whole app at src/backend and look plausible while
    # being wrong. None makes an unconfigured vault fail loudly at the call
    # site if setup mode is ever bypassed, instead of quietly reading and
    # WRITING notes into the wrong folder.
    vault_path: Path | None = None
    self_email: str = ""
    # Outbound direction (Second Brain calling INTO Hermes' own local
    # backend, https://github.com/nousresearch/hermes-agent -- the reverse
    # (the removed inbound MCP direction, which authenticated Hermes calling
    # IN). Port 9119 is `hermes serve`'s own real default (confirmed live,
    # 2026-08-20 -- NOT port 8642/a REST-API-gateway shape as originally
    # researched; that description didn't match this installed version at
    # all). hermes_api_key is an optional manual override only --
    # app/hermes/rest.py's real, default path fetches the session token
    # itself (embedded in `GET /`'s own HTML, confirmed live), since
    # that's the actual mechanism this server uses, not a pre-issued key.
    hermes_base_url: str = "http://127.0.0.1:9119"
    hermes_api_key: str = ""
    # Local filesystem root of the real Hermes install (2026-08-22) --
    # distinct from hermes_base_url above: that's Hermes' own live API
    # (`hermes serve`, port 9119), which today only exposes session/status/
    # active-profile data, not full Agent/Skill definitions. Reading these
    # DIRECTLY from Hermes' own real files (profile.yaml/config.yaml/
    # SOUL.md per profile, SKILL.md per skill) is the operator's own
    # explicit choice for app/hermes/definitions.py -- always current, no sync
    # step. Default matches this machine's real install path; override via
    # .env on a different machine.
    hermes_home_path: Path = Path.home() / "AppData" / "Local" / "hermes"
    # App's own operational-state folder (System settings page, 2026-08-27)
    # -- deliberately independent of vault_path so it can be relocated
    # without moving the vault. `None` means "not set via .env"; the
    # validator below then defaults it to the historical
    # <vault_path>/.second-brain location, so an existing install keeps
    # working unchanged until the operator explicitly moves it from the
    # System settings page (system_settings.py owns the real folder move).
    second_brain_data_path: Path | None = None
    # Comma-separated frontend origins allowed to call this API
    # (main.py's CORS middleware). Default matches the two Vite dev ports
    # this repo actually ships with -- override via .env for any other
    # deployment target.
    cors_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    @model_validator(mode="after")
    def _default_second_brain_data_path(self) -> "Settings":
        # `vault_path is None` only happens before setup has run; deriving the
        # historical <vault>/.second-brain default is meaningless then, so it
        # is left unset rather than guessed at.
        if self.second_brain_data_path is None and self.vault_path is not None:
            self.second_brain_data_path = self.vault_path / ".second-brain"
        return self

    @property
    def missing_required_settings(self) -> list[str]:
        """Which of REQUIRED_FOR_STARTUP have no real value yet -- the setup
        wizard's own worklist, and the reason setup mode is on."""
        return [name for name in REQUIRED_FOR_STARTUP if not getattr(self, name)]

    @property
    def setup_required(self) -> bool:
        return bool(self.missing_required_settings)

    @property
    def compass_embeddings_endpoint(self) -> str:
        """The embeddings route, derived from the configured chat route
        unless explicitly overridden. `compass_base_url` is a FULL route
        (".../v1/chat/completions"), not a base -- an install that pointed
        the two at the same URL would send every embedding request to the
        chat endpoint and fail with a confusing model error, so the
        chat-specific tail is swapped rather than appended to."""
        if self.compass_embeddings_url:
            return self.compass_embeddings_url.strip()
        base = self.compass_base_url.strip()
        if not base:
            return ""
        return base.removesuffix("/").removesuffix("/chat/completions") + "/embeddings"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()

# The canonical vault engine is standalone by design -- stdlib only, no
# backend import -- so it resolves the App Database Folder from the
# ENVIRONMENT (vault_manager.data_root), exactly as it does inside a Hermes
# worker. pydantic loads .env into Settings without exporting to os.environ,
# so in-process it would fall back to <vault>/.second-brain and silently look
# for Templates in a directory that has not existed since the 2026-09-03
# config/vault split. Export it here so the engine behaves identically in
# this process and in Hermes.
if settings.second_brain_data_path:
    os.environ.setdefault("SECOND_BRAIN_DATA_PATH", str(settings.second_brain_data_path))
