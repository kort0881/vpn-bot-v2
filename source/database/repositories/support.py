from collections.abc import Sequence
from typing import Any

from sqlalchemy import func
from sqlalchemy import select

from ..models import SupportMessageOrm
from .base import AbstractRepository


class SupportRepository(AbstractRepository[SupportMessageOrm, int]):
    model = SupportMessageOrm

    async def add(self, data: dict[str, Any]) -> SupportMessageOrm:
        msg = self.model(**data)
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def get(self, obj_id: int) -> SupportMessageOrm | None:
        return await self.get_by_filters(id=obj_id)

    async def update(
        self, obj_id: int, data: dict[str, Any]
    ) -> SupportMessageOrm | None:
        msg = await self.get(obj_id)
        if msg:
            for key, value in data.items():
                if hasattr(msg, key) and key != "id":
                    setattr(msg, key, value)
        return msg

    async def delete(self, **filters: Any) -> None:
        await self.delete_by_filters(**filters)

    async def add_by_filters(self, data: dict[str, Any]) -> SupportMessageOrm:
        return await self.add(data)

    async def get_by_filters(self, **filters: Any) -> SupportMessageOrm | None:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalar_one_or_none()

    async def update_by_filters(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Sequence[SupportMessageOrm]:
        rows = await self.list_by_filters(**filters)
        for row in rows:
            for key, value in data.items():
                if hasattr(row, key) and key != "id":
                    setattr(row, key, value)
        return rows

    async def delete_by_filters(self, **filters: Any) -> None:
        for row in await self.list_by_filters(**filters):
            await self.session.delete(row)

    async def list_by_filters(self, **filters: Any) -> Sequence[SupportMessageOrm]:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalars().all()

    async def list_new(self, limit: int = 20) -> Sequence[SupportMessageOrm]:
        stmt = (
            select(self.model)
            .where(self.model.status == "new")
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
