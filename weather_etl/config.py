import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    REDIS_URL: str = os.environ["REDIS_URL"]

    # API
    API_HOST: str = os.environ["API_HOST"]
    API_PORT: int = int(os.environ["API_PORT"])

    # Security
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    ENCRYPTION_KEY: str = os.environ["ENCRYPTION_KEY"]

    # Features
    DATA_QUALITY_ENABLED: bool = os.environ["DATA_QUALITY_ENABLED"].lower() == "true"
    METRICS_ENABLED: bool = os.environ["METRICS_ENABLED"].lower() == "true"

    @property
    def encryption_key_bytes(self) -> bytes:
        # Convert string key to bytes for Fernet
        return self.ENCRYPTION_KEY.encode()


settings = Settings()
