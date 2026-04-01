import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import create_app
from app.config.db import Base, attach_sqlite_pragmas
from app.repositories.user_repository import UserRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.token_repository import TokenRepository

TEST_DATABASE_URL = 'sqlite+aiosqlite:///test.db'


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    attach_sqlite_pragmas(engine, TEST_DATABASE_URL)
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


@pytest_asyncio.fixture
async def token_repository(async_session):
    return TokenRepository(async_session)


@pytest_asyncio.fixture
async def setup_factory_session(async_session: AsyncSession):

    from tests import factories

    factory_list = [
        factories.UserFactory,
        factories.ContactFactory,
        factories.PasswordResetTokenFactory,
    ]

    for factory in factory_list:
        factory._meta.sqlalchemy_session = async_session

    yield

    for factory in factory_list:
        factory._meta.sqlalchemy_session = None


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
