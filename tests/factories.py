from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
import factory
from factory import Faker, LazyFunction, SubFactory

from app.models.user import User
from app.models.contact import Contact
from app.models.password_reset_token import PasswordResetToken
from app.schemas.schemas import (
    LoginSchema,
    UserRequest,
    ContactRequest,
    ResetPasswordRequest,
    EmailSchema,
)
from datetime import datetime, timezone, timedelta


class BaseAsyncFactory(AsyncSQLAlchemyFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None
        sqlalchemy_session_persistence = 'flush'


class UserFactory(BaseAsyncFactory):
    class Meta:
        model = User

    name = Faker('name')
    email = Faker('email')
    password = 'hashed_password_placeholder'

    @factory.post_generation
    def with_contact(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted is True:
            ContactFactory.create(user=obj, **kwargs)

    @factory.post_generation
    def with_token(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted is True:
            PasswordResetTokenFactory.create(user=obj, **kwargs)


class ContactFactory(BaseAsyncFactory):
    class Meta:
        model = Contact

    user = SubFactory(UserFactory)
    name = Faker('name')
    phone = Faker('numerify', text='###########')
    email = Faker('email')


class PasswordResetTokenFactory(BaseAsyncFactory):
    class Meta:
        model = PasswordResetToken

    user = SubFactory(UserFactory)
    token_hash = Faker('uuid4')
    expires_at = LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(minutes=30)
    )


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
    phone = Faker('numerify', text='###########')
    email = Faker('email')


class LoginFactory(factory.Factory):
    class Meta:
        model = LoginSchema

    email = Faker('email')
    password = Faker('password', length=12)


class ResetPasswordRequestFactory(factory.Factory):
    class Meta:
        model = ResetPasswordRequest

    new_password = 'NewSecurePassword123!'
    token = Faker('uuid4')


class EmailSchemaFactory(factory.Factory):
    class Meta:
        model = EmailSchema

    email = Faker('email')
