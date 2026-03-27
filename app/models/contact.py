from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.db import Base

if TYPE_CHECKING:
    from app.models.user import User


class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, default='Person')
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False, index=True
    )
    user: Mapped['User'] = relationship(back_populates='contacts')

    def __init__(self, name: str, phone: str | None, email: str | None):
        self.name = name.strip()
        self.phone = phone
        self.email = email.strip().lower() if email else None
