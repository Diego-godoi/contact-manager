import asyncio
from typing import TYPE_CHECKING, List

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.config.db import Base

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.password_reset_token import PasswordResetToken


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    contacts: Mapped[List['Contact']] = relationship(
        back_populates='user',
        lazy='noload',
        cascade='all, delete-orphan',
    )
    password_reset_tokens: Mapped[List['PasswordResetToken']] = relationship(
        back_populates='user', lazy='noload', cascade='all, delete-orphan'
    )

    @validates('name')
    def validate_name(self, key, value):
        if value:
            return value.strip()
        return value

    @validates('email')
    def validate_email(self, key, value):
        if value:
            return value.strip().lower()
        return value

    async def set_password(self, password):
        self.password = await asyncio.to_thread(
            lambda: hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
        )

    async def check_password(self, password):
        return await asyncio.to_thread(
            lambda: checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        )
