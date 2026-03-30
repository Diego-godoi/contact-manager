from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

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

    @validates('phone')
    def validate_phone(self, key, value):
        if value:
            return value.strip()
        return value
