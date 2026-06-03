import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Auth Service Configuration"""
    
    # Server
    AUTH_SERVICE_PORT: int = int(os.getenv("AUTH_SERVICE_PORT", 8001))
    DEBUG: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    AUTH_DB_URL: str = os.getenv("AUTH_DB_URL", "postgresql://user:password@localhost/auth_db")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
    JWT_REFRESH_EXPIRATION_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", 30))
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
