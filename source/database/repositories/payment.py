from collections.abc import Sequence
from typing import Any

from sqlalchemy import func
from sqlalchemy import select

from ..models import PaymentOrm
from .base import AbstractRepository




class PaymentRepository(AbstractRepository[PaymentOrm, int]):
    model = PaymentOrm

    async def add(self, data: dict[str, Any]) -> PaymentOrm:
        payment = self.model(**data)
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get(self, obj_id: int) -> PaymentOrm | None:
        return await self.get_by_filters(id=obj_id)

    async def update(self, obj_id: int, data: dict[str, Any]) -> PaymentOrm | None:
        payment = await self.get(obj_id)
        if payment:
            for key, value in data.items():
                if hasattr(payment, key) and key != "id":
                    setattr(payment, key, value)
        return payment

    async def delete(self, **filters: Any) -> None:
        await self.delete_by_filters(**filters)

    async def add_by_filters(self, data: dict[str, Any]) -> PaymentOrm:
        return await self.add(data)

    async def get_by_filters(self, **filters: Any) -> PaymentOrm | None:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalar_one_or_none()

    async def update_by_filters(
        self, filters: dict[str, Any], data: dict[str, Any]
    ) -> Sequence[PaymentOrm]:
        rows = await self.list_by_filters(**filters)
        for row in rows:
            for key, value in data.items():
                if hasattr(row, key) and key != "id":
                    setattr(row, key, value)
        return rows

    async def delete_by_filters(self, **filters: Any) -> None:
        for row in await self.list_by_filters(**filters):
            await self.session.delete(row)

    async def list_by_filters(self, **filters: Any) -> Sequence[PaymentOrm]:
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalars().all()

    async def list_recent(self, limit: int = 50) -> Sequence[PaymentOrm]:
        stmt = select(self.model).order_by(self.model.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def total_confirmed(self) -> int:
        stmt = select(func.coalesce(func.sum(self.model.amount), 0)).where(
            self.model.status == "confirmed"
        )
        return int(await self.session.scalar(stmt) or 0)
