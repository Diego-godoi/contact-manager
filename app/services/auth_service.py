from app.services.email_service import EmailService
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.config.jwt import create_tokens
from app.errors.exceptions import NotFoundError, InvalidCredentialsError
import secrets
from app.repositories.token_repository import TokenRepository
from datetime import timedelta, datetime, timezone


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: TokenRepository,
        email_service: EmailService,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.email_service = email_service

    async def login_user(self, data):
        user: User = await self.user_repo.find_by_email(data.email)
        if user is None:
            raise NotFoundError(detail='User not found')

        if not await user.check_password(data.password):
            raise InvalidCredentialsError(detail='Invalid password')

        return create_tokens(user.id)

    async def get_user(self, id: int):
        user = await self.user_repo.find_by_id(id)
        if not user:
            raise NotFoundError(detail='User not found')
        return user

    async def email_forgot_password_link(self, data, background_tasks):
        user = await self.user_repo.find_by_email(data.email)

        if user is None:
            raise NotFoundError(detail='User not found')

        raw_token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)

        token = PasswordResetToken(user_id=user.id, expires_at=expires)
        await token.set_token(raw_token)

        await self.token_repo.save(token)

        background_tasks.add_task(
            self.email_service.send_password_reset_email, user, raw_token
        )

    async def reset_password(self, data):
        token = await self.token_repo.find_by_token_hash(data.token)
        if token is None:
            raise NotFoundError(detail='Token not found')

        if token.is_expired:
            await self.token_repo.delete(token.id)
            raise InvalidCredentialsError(detail='Token has expired')

        user = await self.user_repo.find_by_id(token.user_id)
        if user is None:
            raise NotFoundError(detail='User not found')

        await user.set_password(data.new_password)

        await self.user_repo.save(user)

        await self.token_repo.delete(token.id)
