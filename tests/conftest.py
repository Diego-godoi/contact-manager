import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import create_app
from app.config.db import Base
from app.repositories.user_repository import UserRepository
from app.repositories.contact_repository import ContactRepository
from tests.factories import (
    LoginFactory,
    UserFactory,
    UserRequestFactory,
    ContactFactory,
    ContactRequestFactory,
)

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    async_session_maker = async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def user_repository(async_session):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def contact_repository(async_session):
    return ContactRepository(async_session)


@pytest.fixture
def create_contacts():
    def _create_contacts(count=5, **kwargs):
        return ContactFactory.build_batch(count, **kwargs)

    return _create_contacts


@pytest.fixture
def create_user_request():
    def _create_user_request(**kwargs):
        return UserRequestFactory.build(**kwargs)

    return _create_user_request


@pytest.fixture
def create_contact_request():
    def _create_contact_request(**kwargs):
        return ContactRequestFactory.build(**kwargs)

    return _create_contact_request


@pytest.fixture
def create_login():
    def _create_login(**kwargs):
        return LoginFactory.build(**kwargs)

    return _create_login


@pytest.fixture
def create_users():
    def _create_users(count=5, **kwargs):
        return UserFactory.build_batch(count, **kwargs)

    return _create_users


@pytest_asyncio.fixture
async def save_users(async_session):
    async def _save_users(users):
        async_session.add_all(users)
        await async_session.commit()
        for user in users:
            await async_session.refresh(user)
        return users

    return _save_users


@pytest_asyncio.fixture
async def client():
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as c:
        c.app = app
        app.state.limiter.enabled = False

        yield c

        app.dependency_overrides.clear()
