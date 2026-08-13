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


settings = Settings()
