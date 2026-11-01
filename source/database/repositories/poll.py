from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from ..models import PollAnswerOrm
from .base import AbstractRepository


class PollRepository(AbstractRepository[PollAnswerOrm, int]):
    model = PollAnswerOrm

    async def add(self, data: dict[str, Any]) -> PollAnswerOrm:
        row = self.model(**data)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, obj_id: int) -> PollAnswerOrm | None:
        return await self.get_by_filters(id=obj_id)

    async def update(self, obj_id: int, data: dict[str, Any]) -> PollAnswerOrm | None:
        row = await self.get(obj_id)
        if row:
            for k, v in data.items():
                if hasattr(row, k) and k != "id":
                    setattr(row, k, v)
        return row

    async def delete(self, **filters: Any) -> None:
        await self.delete_by_filters(**filters)

    async def add_by_filters(self, data: dict[str, Any]) -> PollAnswerOrm:
        return await self.add(data)

    async def get_by_filters(self, **filters: Any) -> PollAnswerOrm | None:
        res = await self.session.execute(select(self.model).filter_by(**filters))
        return res.scalar_one_or_none()

    async def update_by_filters(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Sequence[PollAnswerOrm]:
        rows = await self.list_by_filters(**filters)
        for row in rows:
            for k, v in data.items():
                if hasattr(row, k) and k != "id":
                    setattr(row, k, v)
        return rows

    async def delete_by_filters(self, **filters: Any) -> None:
        for row in await self.list_by_filters(**filters):
            await self.session.delete(row)

    async def list_by_filters(self, **filters: Any) -> Sequence[PollAnswerOrm]:
        res = await self.session.execute(select(self.model).filter_by(**filters))
        return res.scalars().all()

    async def count_by_poll(self, poll_id: str) -> int:
        rows = await self.list_by_filters(poll_id=poll_id)
        return len(rows)
