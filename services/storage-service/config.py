import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Storage Service Configuration"""
    
    # Server
    STORAGE_SERVICE_PORT: int = int(os.getenv("STORAGE_SERVICE_PORT", 8003))
    DEBUG: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database
    STORAGE_DB_URL: str = os.getenv("STORAGE_DB_URL", "postgresql://user:password@localhost/storage_db")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
