import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str = "postgresql://postgres:Postgres%4012345@localhost:5432/krushirakshak"
    db_echo: bool = False
    secret_key: str = "change-me"
    weather_api_key: str = ""
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
