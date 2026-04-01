from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.models.password_reset_token import PasswordResetToken


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, data):
        try:
            self.session.add(data)
            await self.session.commit()
            await self.session.refresh(data)
            return data
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error saving password reset token to database: {str(e)}')

    async def find_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        try:
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f'Error finding token: {str(e)}')

    async def delete_all_by_user_id(self, user_id: int) -> int:
        try:
            stmt = delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user_id
            )
            result = await self.session.execute(
                stmt, execution_options={'synchronize_session': 'evaluate'}
            )
            await self.session.commit()
            return result.rowcount
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error deleting user reset tokens: {str(e)}')

    async def replace_all_by_user_id(
        self, user_id: int, new_token: PasswordResetToken
    ) -> PasswordResetToken:
        try:
            await self.session.execute(
                delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
            )

            self.session.add(new_token)
            await self.session.commit()
            await self.session.refresh(new_token)

            return new_token
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error replacing password reset tokens: {str(e)}')
