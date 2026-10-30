from collections.abc import Sequence
from typing import Any

from sqlalchemy import func
from sqlalchemy import select

from ..models import StatOrm
from .base import AbstractRepository


class StatRepository(AbstractRepository[StatOrm, str]):
    model = StatOrm

    async def add(self, data: dict[str, Any]) -> StatOrm:
        stat = self.model(**data)
        self.session.add(stat)
        await self.session.flush()
        return stat

    async def get(self, obj_id: str) -> StatOrm | None:
        return await self.get_by_filters(key=obj_id)

    async def update(self, obj_id: str, data: dict[str, Any]) -> StatOrm | None:
        stat = await self.get(obj_id)
        if stat:
            for key, value in data.items():
                if hasattr(stat, key) and key != "key":
                    setattr(stat, key, value)
        return stat

    async def delete(self, **filters: Any) -> None:
        await self.delete_by_filters(**filters)

    async def add_by_filters(self, data: dict[str, Any]) -> StatOrm:
        return await self.add(data)

    async def get_by_filters(self, **filters: Any) -> StatOrm | None:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalar_one_or_none()

    async def update_by_filters(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Sequence[StatOrm]:
        rows = await self.list_by_filters(**filters)
        for row in rows:
            for key, value in data.items():
                if hasattr(row, key) and key != "key":
                    setattr(row, key, value)
        return rows

    async def delete_by_filters(self, **filters: Any) -> None:
        for row in await self.list_by_filters(**filters):
            await self.session.delete(row)

    async def list_by_filters(self, **filters: Any) -> Sequence[StatOrm]:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalars().all()

    async def incr(self, key: str, delta: int = 1) -> int:
        stat = await self.get(key)
        if stat is None:
            stat = await self.add({"key": key, "value": delta})
        else:
            stat.value = int(stat.value or 0) + delta
        return int(stat.value)

    async def get_value(self, key: str) -> int:
        stat = await self.get(key)
        return int(stat.value) if stat else 0
