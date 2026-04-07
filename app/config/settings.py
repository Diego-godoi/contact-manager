from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from pathlib import Path


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # APP
    APP_NAME: str = 'Contact Manager'

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_USER: str = 'diego'
    POSTGRES_PASSWORD: str = '123'
    POSTGRES_DB: str = 'contact_manager'
    POSTGRES_PORT: str = '5432'

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

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

    # images dir
    IMAGES_DIR: str = 'app/static/profile-picture'

    @computed_field
    @property
    def IMAGES_PATH(self) -> Path:
        path = Path(self.IMAGES_DIR)
        if path.is_absolute():
            return path
        return self.BASE_DIR / path

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', case_sensitive=True, extra='ignore'
    )


settings = Settings()
