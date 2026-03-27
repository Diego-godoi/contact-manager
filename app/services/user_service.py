from app.config.jwt import create_tokens
from app.errors.exceptions import (
    ConflictError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, data) -> User:
        if await self.repository.exists_by_email(data.email):
            raise ConflictError(detail='Email already exists')

        user = User(name=data.name, email=data.email, password='')
        await user.set_password(data.password)
        return await self.repository.save(user)

    async def update_user(self, id: int, data) -> User:
        user: User = await self.repository.find_by_id(id)

        if user is None:
            raise NotFoundError(detail='User not found')

        if data.email is not None and user.email != data.email:
            if await self.repository.exists_by_email(data.email):
                raise ConflictError(detail='Email already exists')

            user.email = data.email

        if data.password is not None:
            await user.set_password(data.password)

        if data.name is not None and user.name != data.name:
            user.name = data.name

        return await self.repository.save(user)

    async def delete_user(self, id: int) -> bool:
        if not await self.repository.exists_by_id(id):
            raise NotFoundError(detail='User not found')

        return await self.repository.delete(id)

    async def get_all_users(self, page, per_page):
        items, total = await self.repository.get_all(page, per_page)
        pages = (total + per_page - 1) // per_page
        return items, total, pages

    async def login_user(self, data):
        user: User = await self.repository.find_by_email(data.email)
        if user is None:
            raise NotFoundError(detail='User not found')

        if not await user.check_password(data.password):
            raise InvalidCredentialsError(detail='Invalid password')

        return create_tokens(user.id)

    async def get_user(self, id: int):
        user = await self.repository.find_by_id(id)
        if not user:
            raise NotFoundError(detail='User not found')
        return user
