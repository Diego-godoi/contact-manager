from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.config.jwt import create_tokens
from app.errors.exceptions import NotFoundError, InvalidCredentialsError
import secrets
from app.repositories.token_repository import TokenRepository
from datetime import timedelta, datetime, timezone
from app.schemas.schemas import LoginSchema, EmailSchema, ResetPasswordRequest


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: TokenRepository,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def login_user(self, data: LoginSchema):
        user: User = await self.user_repo.find_by_email(data.email)
        if user is None:
            raise InvalidCredentialsError(detail='Invalid email or password')

        if not await user.check_password(data.password):
            raise InvalidCredentialsError(detail='Invalid email or password')

        return create_tokens(user.id)

    async def get_user(self, id: int):
        user = await self.user_repo.find_by_id(id)
        if not user:
            raise NotFoundError(detail='User not found')
        return user

    async def prepare_password_reset(self, data: EmailSchema):
        user = await self.user_repo.find_by_email(data.email)

        raw_token = secrets.token_urlsafe(32)
        if user is None:
            return None

        expires = datetime.now(timezone.utc) + timedelta(minutes=30)

        token = PasswordResetToken(user_id=user.id, expires_at=expires)
        await token.set_token(raw_token)

        await self.token_repo.replace_all_by_user_id(user.id, token)

        return (user, raw_token)

    async def reset_password(self, data: ResetPasswordRequest):
        hashed_token: str = await PasswordResetToken.hash_token(data.token)
        token = await self.token_repo.find_by_token_hash(hashed_token)
        if token is None:
            raise NotFoundError(detail='Token not found')

        if token.is_expired:
            await self.token_repo.delete_all_by_user_id(token.user_id)
            raise InvalidCredentialsError(detail='Token has expired')

        user = await self.user_repo.find_by_id(token.user_id)
        if user is None:
            await self.token_repo.delete_all_by_user_id(token.user_id)
            raise NotFoundError(detail='User not found')

        await user.set_password(data.new_password)

        await self.user_repo.save(user)

        await self.token_repo.delete_all_by_user_id(user.id)
