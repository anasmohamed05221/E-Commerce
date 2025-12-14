from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()