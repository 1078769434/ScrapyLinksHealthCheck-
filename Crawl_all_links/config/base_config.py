from pathlib import Path

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_DIR: Path = PROJECT_DIR

    START_URL: str
    DEPTH_LIMIT: int
    DOWNLOAD_DELAY: int
    HTTPERROR_ALLOW_ALL: bool = True
    CONCURRENT_REQUESTS: int


    # postgres database
    POSTGRES_URL: PostgresDsn = "postgresql+asyncpg://localhost/watchai"


    model_config = SettingsConfigDict(env_file=f"{PROJECT_DIR}/.env", extra="ignore")


settings = Settings()

