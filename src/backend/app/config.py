from pathlib import Path

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
    # hermes_client.py's real, default path fetches the session token
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
    # explicit choice for hermes_definitions.py -- always current, no sync
    # step. Default matches this machine's real install path; override via
    # .env on a different machine.
    hermes_home_path: Path = Path.home() / "AppData" / "Local" / "hermes"


settings = Settings()
