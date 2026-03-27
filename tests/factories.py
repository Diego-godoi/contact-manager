import factory
from factory import Faker

from app.models.user import User
from app.models.contact import Contact
from app.schemas.schemas import LoginSchema, UserRequest, ContactRequest


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
