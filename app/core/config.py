from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Rachel Capital OS Platform"
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "rachel_capital"
    postgres_user: str = "rachel"
    postgres_password: str = "change_me"

    database_url: str = Field(default="sqlite:///./data/rachel_capital.db")

    obsidian_vault_path: str | None = None
    coze_webhook_secret: str | None = None
    feishu_webhook_url: str | None = None
    github_token: str | None = None
    tushare_token: str | None = None
    alpha_vantage_api_key: str | None = None
    fred_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
