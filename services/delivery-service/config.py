import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Delivery Service Configuration"""
    
    # Server
    DELIVERY_SERVICE_PORT: int = int(os.getenv("DELIVERY_SERVICE_PORT", 8004))
    DEBUG: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # SMTP Configuration
    SMTP_PROVIDER: str = os.getenv("SMTP_PROVIDER", "sendgrid")  # sendgrid, mailgun, postmark, etc.
    SMTP_API_KEY: str = os.getenv("SMTP_API_KEY", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@micromail.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "MicroMail")
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 5))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", 60))
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
