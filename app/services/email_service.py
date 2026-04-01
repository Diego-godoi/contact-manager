from fastapi_mail import FastMail, MessageSchema, MessageType
from app.config.settings import settings
from app.models.user import User


class EmailService:
    def __init__(self, mail_engine: FastMail):
        self.fm = mail_engine

    async def send_password_reset_email(self, user: User, token: str):
        reset_url = (
            f'{settings.FRONTEND_HOST}/reset-password?token={token}&email={user.email}'
        )

        data = {
            'app_name': settings.APP_NAME,
            'name': user.name,
            'activate_url': reset_url,
        }
        subject = f'Reset Password - {settings.APP_NAME}'

        message = MessageSchema(
            subject=subject,
            recipients=[user.email],
            template_body=data,
            subtype=MessageType.html,
        )

        await self.fm.send_message(message, template_name='user/password-reset.html')
