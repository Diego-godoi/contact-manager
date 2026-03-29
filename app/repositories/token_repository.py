from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.models.password_reset_token import PasswordResetToken
import hashlib


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

    async def delete(self, token_id: int):
        try:
            stmt = delete(PasswordResetToken).where(PasswordResetToken.id == token_id)
            result = await self.session.execute(
                stmt, execution_options={'synchronize_session': 'evaluate'}
            )
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise ValueError(
                f'Error deleting password reset token to database: {str(e)}'
            )

    async def find_by_token_hash(self, raw_token: str):
        try:
            target_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            stmt = select(PasswordResetToken).where(
                PasswordResetToken.token_hash == target_hash
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(
                f'Error finding password reset token by id to database: {str(e)}'
            )
