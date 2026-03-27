from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, data: User) -> User:
        try:
            self.session.add(data)
            await self.session.commit()
            await self.session.refresh(data)
            return data
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error saving user to database: {str(e)}')

    async def delete(self, user_id: int):
        try:
            stmt = delete(User).where(User.id == user_id)

            result = await self.session.execute(
                stmt, execution_options={'synchronize_session': 'evaluate'}
            )  # Deleta tanto no sql tanto no cache - Nao sincroniza com a session
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error deleting user to database: {str(e)}')

    async def get_all(self, page: int, per_page: int):
        try:
            stmt_users = (
                select(User)
                .order_by(User.id)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            result_users = await self.session.execute(stmt_users)
            users = result_users.scalars().all()

            stmt_count = select(func.count()).select_from(User)
            result_count = await self.session.execute(stmt_count)
            total = result_count.scalar()

            return users, total
        except Exception as e:
            raise ValueError(f'Error getting all users from database: {str(e)}')

    async def exists_by_email(self, email: str) -> bool:
        try:
            stmt = select(exists().where(User.email == email.lower()))
            result = await self.session.execute(stmt)

            return result.scalar()
        except Exception as e:
            raise ValueError(f'Error getting user by email to database: {str(e)}')

    async def exists_by_id(self, user_id: int) -> bool:
        try:
            stmt = select(exists().where(User.id == user_id))
            result = await self.session.execute(stmt)
            return result.scalar()
        except Exception as e:
            raise ValueError(f'Error getting user by id to database: {str(e)}')

    async def find_by_id(self, user_id: int):
        try:
            user = await self.session.get(User, user_id)
            return user
        except Exception as e:
            raise ValueError(f'Error finding user by id to database: {str(e)}')

    async def find_by_email(self, email: str):
        try:
            stmt = select(User).where(User.email == email).limit(1)
            user = (await self.session.execute(stmt)).scalar()
            return user
        except Exception as e:
            raise ValueError(f'Error finding user by email to database: {str(e)}')
