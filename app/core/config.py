import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


def initialize_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s",
    )


class Settings(BaseSettings):
    ENV: str = "dev"
    VERSION: str = "v1"
    ENABLE_DOCS: bool = True
    DEBUG: bool = True
    DATABASE_URL: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf_8",
    )


config = Settings()
