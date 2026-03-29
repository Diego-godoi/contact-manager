import factory
from factory import Faker, LazyFunction

from app.models.user import User
from app.models.contact import Contact
from app.models.password_reset_token import PasswordResetToken
from app.schemas.schemas import (
    LoginSchema,
    UserRequest,
    ContactRequest,
    EmailSchema,
    ResetPasswordRequest,
)
from datetime import datetime, timezone, timedelta


class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = Faker('name')
    email = Faker('email')
    password = Faker('password', length=12)


class ContactFactory(factory.Factory):
    class Meta:
        model = Contact

    name = Faker('name')
    phone = Faker('bothify', text='###########')
    email = Faker('email')


class UserRequestFactory(factory.Factory):
    class Meta:
        model = UserRequest

    name = Faker('name')
    email = Faker('email')
    password = Faker('password', length=12)


class ContactRequestFactory(factory.Factory):
    class Meta:
        model = ContactRequest

    name = Faker('name')
    phone = Faker('bothify', text='###########')
    email = Faker('email')


class LoginFactory(factory.Factory):
    class Meta:
        model = LoginSchema

    email = Faker('email')
    password = Faker('password', length=12)


class PasswordResetTokenFactory(factory.Factory):
    class Meta:
        model = PasswordResetToken

    token_hash = Faker('uuid4')
    expires_at = LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(minutes=30)
    )


class EmailSchemaFactory(factory.Factory):
    class Meta:
        model = EmailSchema

    email = Faker('email')


class ResetPasswordRequestFactory(factory.Factory):
    class Meta:
        model = ResetPasswordRequest

    new_password = Faker('password')
    token = Faker('uuid4')
