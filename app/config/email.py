from pathlib import Path
from fastapi_mail import FastMail, ConnectionConfig
from app.config.settings import settings

# Configuração centralizada
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    MAIL_DEBUG=settings.MAIL_DEBUG,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=settings.SUPPRESS_SEND,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates',
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
)

# Instância global do motor de e-mail
fm = FastMail(conf)
