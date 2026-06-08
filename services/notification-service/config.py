from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MicroMail Notification Service"
    PORT: int = 8005
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    # Menggunakan port 5435 sesuai dengan yang kita expose di docker-compose
    DATABASE_URL: str = "postgresql://notification_user:notification_password@localhost:5435/notification_db"

    class Config:
        env_file = ".env"

settings = Settings()