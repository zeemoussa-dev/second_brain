from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    compass_base_url: str
    compass_api_key: str
    compass_model: str
    anthropic_api_key: str
    anthropic_model: str
    vault_path: Path
    self_email: str
    hermes_mcp_shared_secret: str
    # Outbound direction (Second Brain calling INTO Hermes' own local
    # backend, https://github.com/nousresearch/hermes-agent -- the reverse
    # of hermes_mcp_shared_secret above, which authenticates Hermes calling
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
        if self.second_brain_data_path is None:
            self.second_brain_data_path = self.vault_path / ".second-brain"
        return self

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
