import asyncio
from typing import TYPE_CHECKING, List

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.db import Base

if TYPE_CHECKING:
    from app.models.contact import Contact


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

    def __init__(self, name: str, email: str, password: str):
        self.name = name.strip()
        self.email = email.strip().lower()
        self.password = password

    async def set_password(self, password):
        self.password = await asyncio.to_thread(
            lambda: hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
        )

    async def check_password(self, password):
        return await asyncio.to_thread(
            lambda: checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        )
