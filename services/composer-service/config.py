import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Composer Service Configuration"""
    
    # Server
    COMPOSER_SERVICE_PORT: int = int(os.getenv("COMPOSER_SERVICE_PORT", 8002))
    DEBUG: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    COMPOSER_DB_URL: str = os.getenv("COMPOSER_DB_URL", "postgresql://user:password@localhost/composer_db")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
