from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AUTH_SERVICE_PORT: int = 8001
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    AUTH_DB_URL: str

    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24  # kept for backward compat; prefer JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # default 24h
    JWT_REFRESH_EXPIRATION_DAYS: int = 30

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()