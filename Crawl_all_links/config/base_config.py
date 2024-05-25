from pathlib import Path

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_DIR: Path = PROJECT_DIR

    # postgres database
    POSTGRES_URL: PostgresDsn = str

    REDIS_DB_HOST: str
    REDIS_DB_PWD: str = ""

    # 快代理用户名和密码
    KUAIDAILI_USERNAME: str = ""
    KUAIDAILI_PASSWORD: str = ""

    # 快代理密钥
    SECRET_ID: str = ""
    SIGNATURE: str = ""

    model_config = SettingsConfigDict(env_file=f"{PROJECT_DIR}/.env", extra="ignore")


settings = Settings()
