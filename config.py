from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_ENGINE: str
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    SECRET_KEY: str
    ALGORITHM: str
    ORIGINS: list[str] = []
    ALLOWED_HOSTS: list[str] = []
    API_DOMAIN: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        return f"{self.DATABASE_ENGINE}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}/{self.DATABASE_NAME}"


settings = Settings()

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

COURSES_DIR = MEDIA_DIR / "courses"
COURSES_DIR.mkdir(parents=True, exist_ok=True)
