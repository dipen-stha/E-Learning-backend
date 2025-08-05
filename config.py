from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_ENGINE: str
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    SECRET_KEY: str
    ALGORITHM: str

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"{self.DATABASE_ENGINE}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}/{self.DATABASE_NAME}"

settings = Settings()