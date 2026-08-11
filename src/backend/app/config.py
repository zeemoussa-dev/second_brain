from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    compass_base_url: str
    compass_api_key: str
    compass_model: str
    vault_path: Path


settings = Settings()
