from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MAIL_SERVICE_PORT: int = 8004
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    RABBITMQ_URL: str

    class Config:
        env_file = ".env"


settings = Settings()