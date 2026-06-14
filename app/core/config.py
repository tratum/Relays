from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"


class Settings(BaseSettings):
    ENV: Environment
    VERSION: str
    ENABLE_DOCS: bool
    DATABASE_URL: str
    REDIS_URL: str

    @property
    def DEBUG(self) -> bool:
        return self.ENV == Environment.DEV

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf_8",
    )


config = Settings()
