import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """API Gateway Configuration"""
    
    # Server
    API_GATEWAY_PORT: int = int(os.getenv("API_GATEWAY_PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Service URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    COMPOSER_SERVICE_URL: str = os.getenv("COMPOSER_SERVICE_URL", "http://localhost:8002")
    STORAGE_SERVICE_URL: str = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8003")
    DELIVERY_SERVICE_URL: str = os.getenv("DELIVERY_SERVICE_URL", "http://localhost:8004")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
