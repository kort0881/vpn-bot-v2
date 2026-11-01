from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from .models import *
from .repositories import *
from .tools.uow import AbstractUnitOfWork as AbstractUnitOfWork
from .tools.uow import UnitOfWork as UnitOfWork

__all__ = [
    "AbstractUnitOfWork",
    "UnitOfWork",
    "auto_migrate",
    "create_tables",
    "drop_tables",
]


async def create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully")


async def drop_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Tables dropped successfully")


async def auto_migrate(engine: AsyncEngine) -> list[str]:
    """Аддитивная миграция при старте: создать недостающие таблицы и колонки.

    Ничего не удаляет и не меняет типы — только добавляет. Этого достаточно,
    чтобы новая версия кода не падала на старой схеме.
    """
    dialect = engine.dialect
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _sync(sync_conn) -> list[str]:
            from sqlalchemy import inspect

            inspector = inspect(sync_conn)
            tables = set(inspector.get_table_names())
            added: list[str] = []
            for table in Base.metadata.sorted_tables:
                if table.name not in tables:
                    continue
                have = {col["name"] for col in inspector.get_columns(table.name)}
                for column in table.columns:
                    if column.name in have:
                        continue
                    ddl = column.type.compile(dialect=dialect)
                    sync_conn.exec_driver_sql(
                        f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {ddl}'
                    )
                    added.append(f"{table.name}.{column.name}")
            return added

        added = await conn.run_sync(_sync)

    if added:
        logger.warning(f"автомиграция: добавлены колонки {added}")
    else:
        logger.info("автомиграция: схема в порядке")
    return added
