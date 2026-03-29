from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # APP
    APP_NAME: str = 'Contact Manager'

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = 'sqlite+aiosqlite:///contact_manager.sqlite'

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_SERVER: str = 'smtp.gmail.com'
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_DEBUG: bool = True
    MAIL_FROM: str
    MAIL_FROM_NAME: str = 'Contact Manager Support'
    SUPPRESS_SEND: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    MAIL_PORT: int = 587

    # Frontend
    FRONTEND_HOST: str = 'http://localhost:3000'

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', case_sensitive=True
    )


settings = Settings()
