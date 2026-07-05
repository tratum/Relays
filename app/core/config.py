from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"


class Settings(BaseSettings):
    ENV: Environment
    VERSION: str
    ENABLE_DOCS: bool
    REDIS_URL: str
    DATABASE_URL: str
    JWT_ALGORITHM: str
    JWT_SECRET: str
    ## ------------------
    ## Provider Details
    ## ------------------
    MAILRELAY_BASE_URL: str
    MAILRELAY_API_TOKEN: str
    MAILRELAY_SENDER_EMAIL: str
    MAILRELAY_SENDER_NAME: str
    MAILRELAY_REQUEST_TIMEOUT: int
    ## ---------------------
    ## Exponential Backoff
    ## ---------------------
    INITIAL_RETRY_DELAY_SECONDS: int
    MAX_RETRY_DELAY_SECONDS: int

    @property
    def DEBUG(self) -> bool:
        return self.ENV == Environment.DEV

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_file_encoding="utf_8",
    )


config = Settings()
