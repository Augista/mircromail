from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DELIVERY_SERVICE_PORT: int = 8004
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    SMTP_HOST: str = "sendgrid"
    SMTP_PORT: int = 587
    SMTP_NAME: str = "noreply@micromail.com"
    SMTP_PASSWORD: str
    SMTP_TLS: bool = True

    MAX_RETRIES: int = 5
    RETRY_DELAY_SECONDS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()