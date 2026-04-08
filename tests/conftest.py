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
from app.repositories.token_repository import TokenRepository
from sqlalchemy import event
import pytest
from app.repositories.img_repository import ImageRepository
from app.config.db import get_db

TEST_DATABASE_URL = 'sqlite+aiosqlite:///test.db'


# event listens check de integridade de fks quando a conexao for aberta
def _attach_sqlite_pragmas(engine, database_url: str) -> None:
    @event.listens_for(engine.sync_engine, 'connect')
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    _attach_sqlite_pragmas(engine, TEST_DATABASE_URL)
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
async def client(async_session):
    app = create_app()
    app.state.testing = True #Garante o uso do lifespan no ambiente de teste
    app.state.limiter.enabled = False #Desativa o limiter das routes

    async def _get_test_db():
        yield async_session

    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as c:
        c.app = app
        yield c
        app.dependency_overrides.clear()


@pytest.fixture
def image_repo(tmp_path):
    base_dir = tmp_path
    img_dir = base_dir / 'app' / 'static' / 'profile-picture'
    return ImageRepository(base_dir=base_dir, img_dir=str(img_dir))
