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
    # Outbound direction (Second Brain calling INTO Hermes' own REST API
    # gateway, https://github.com/nousresearch/hermes-agent -- the reverse
    # of hermes_mcp_shared_secret above, which authenticates Hermes calling
    # IN). Defaulted rather than required: no Hermes gateway is deployed
    # yet, and hermes_client.py's own callers already degrade honestly
    # (HermesUnavailableError) when the configured URL has nothing
    # listening -- an empty api key is a real, valid "no auth configured
    # yet" state, not an error, until one is issued.
    hermes_base_url: str = "http://127.0.0.1:8642"
    hermes_api_key: str = ""


settings = Settings()
