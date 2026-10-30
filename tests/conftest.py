import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TG__BOT_TOKEN", "test")
os.environ.setdefault("TG__ADMIN_IDS", "[1]")
os.environ.setdefault("TG__WEBHOOK_USE", "False")
os.environ.setdefault("TG__WEBHOOK_PATH", "/telegram")
os.environ.setdefault("WEBHOOK__URL", "https://localhost")
os.environ.setdefault("WEBHOOK__HOST", "0.0.0.0")
os.environ.setdefault("WEBHOOK__PORT", "8443")
os.environ.setdefault("WEBHOOK__PATH", "/webhook")
os.environ.setdefault("WEBHOOK__SECRET", "test_secret")
os.environ.setdefault("DB__HOST", "localhost")
os.environ.setdefault("DB__PORT", "5432")
os.environ.setdefault("DB__USER", "postgres")
os.environ.setdefault("DB__PASSWORD", "postgres")
os.environ.setdefault("DB__NAME", "test_db")
os.environ.setdefault("REDIS__HOST", "localhost")
os.environ.setdefault("REDIS__PORT", "6379")
os.environ.setdefault("REDIS__USER", "default")
os.environ.setdefault("REDIS__PASSWORD", "password")
os.environ.setdefault("REDIS__DB", "0")

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from source.database.models import Base


def _database_url() -> str:
    """
    DSN тестовой БД.

    Тесты идут на реальном PostgreSQL, а не на SQLite: в моделях используются
    типы Postgres (JSONB и др.), которые SQLite компилировать не умеет.
    В CI сервис postgres:15-alpine поднят на localhost:5432 (test_db).
    """
    return (
        f"postgresql+asyncpg://{os.environ['DB__USER']}:{os.environ['DB__PASSWORD']}"
        f"@{os.environ['DB__HOST']}:{os.environ['DB__PORT']}/{os.environ['DB__NAME']}"
    )


@pytest_asyncio.fixture()
async def engine():
    engine = create_async_engine(_database_url(), pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture()
async def session(session_factory):
    async with session_factory() as session:
        yield session
