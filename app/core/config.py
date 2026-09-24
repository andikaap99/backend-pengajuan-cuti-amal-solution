from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # APP_HOST: str = "0.0.0.0"
    # APP_PORT: int = 8001
    DATABASE_URL: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 180
    CORS_ORIGINS: str = "http://localhost,http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


### Mail Configuration
class MailSettings(BaseSettings):
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


mail_settings = MailSettings()
