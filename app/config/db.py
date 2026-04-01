from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from app.config.settings import settings


# event listens check de integridade de fks quando a conexao for aberta
def attach_sqlite_pragmas(engine, database_url: str) -> None:
    if 'sqlite' not in database_url:
        return

    @event.listens_for(engine.sync_engine, 'connect')
    def set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


engine = create_async_engine(settings.DATABASE_URL)

attach_sqlite_pragmas(engine, settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # mantem objetos apos commit
)  # session factory


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
