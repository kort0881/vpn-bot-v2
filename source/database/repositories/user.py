from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import UserOrm
from .base import AbstractRepository


class UserRepository(AbstractRepository[UserOrm, int]):
    model = UserOrm

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    # ------------------------------------------------------------ базовый CRUD
    async def add(self, data: dict[str, Any]) -> UserOrm:
        user = self.model(**data)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("User with this user_id already exists") from exc
        return user

    async def get(self, user_id: int) -> UserOrm | None:
        return await self.get_by_filters(user_id=user_id)

    async def update(self, user_id: int, data: dict[str, Any]) -> UserOrm | None:
        user = await self.get(user_id=user_id)

        if user:
            for key, value in data.items():
                if hasattr(user, key) and key not in ["id", "user_id"]:
                    setattr(user, key, value)
            return user
        return None

    async def delete(self, **filters: Any) -> None:
        await self.delete_by_filters(**filters)

    async def add_by_filters(self, data: dict[str, Any]) -> UserOrm:
        return await self.add(data)

    async def get_by_filters(self, **filters: Any) -> UserOrm | None:
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_by_filters(
        self,
        filters: dict[str, Any],
        data: dict[str, Any],
    ) -> Sequence[UserOrm]:
        stmt = (
            update(self.model)
            .filter_by(**filters)
            .values(**{k: v for k, v in data.items() if k not in ["id", "user_id"]})
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_filters(self, **filters: Any) -> None:
        stmt = delete(self.model).filter_by(**filters)
        await self.session.execute(stmt)

    async def list_by_filters(self, **filters: Any) -> Sequence[UserOrm]:
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ------------------------------------------------------------ VPN-операции
    async def get_by_email(self, email: str) -> UserOrm | None:
        return await self.get_by_filters(email=email)

    async def upsert_user(self, user_id: int, defaults: dict[str, Any] | None = None) -> UserOrm:
        """Вернуть пользователя, создав запись при первом обращении."""
        user = await self.get(user_id)
        if user:
            return user
        data: dict[str, Any] = {"user_id": user_id, "username": "", "email": f"u{user_id}"}
        if defaults:
            data.update(defaults)
        return await self.add(data)

    async def set_username(self, user_id: int, username: str) -> None:
        await self.session.execute(
            update(self.model).where(self.model.user_id == user_id).values(username=username or "")
        )

    async def save_key(
        self,
        user_id: int,
        *,
        email: str,
        client_uuid: str,
        vless_link: str,
        links: list,
        total_bytes: int,
        expiry_at: int,
    ) -> None:
        await self.session.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(
                email=email,
                client_uuid=client_uuid,
                vless_link=vless_link,
                links=links,
                total_bytes=total_bytes,
                expiry_at=expiry_at,
                is_active=True,
            )
        )

    async def set_active(self, user_id: int, active: bool) -> None:
        await self.session.execute(
            update(self.model).where(self.model.user_id == user_id).values(is_active=active)
        )

    async def set_banned(self, user_id: int, banned: bool, reason: str = "", at_ms: int = 0) -> None:
        await self.session.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(banned=banned, ban_reason=reason, ban_at=at_ms)
        )

    async def set_unsubscribed(self, user_id: int, at_ms: int) -> None:
        await self.session.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(unsubscribed_at=at_ms, is_active=False)
        )

    async def update_traffic(self, user_id: int, used_bytes: float) -> None:
        await self.session.execute(
            update(self.model).where(self.model.user_id == user_id).values(used_bytes=used_bytes)
        )

    async def set_channel_step(self, user_id: int, step: int) -> None:
        await self.session.execute(
            update(self.model).where(self.model.user_id == user_id).values(channel_step=step)
        )

    async def set_chosen_channel(self, user_id: int, channel: int) -> None:
        await self.session.execute(
            update(self.model).where(self.model.user_id == user_id).values(chosen_channel=channel)
        )

    async def add_balance(self, user_id: int, amount: int) -> None:
        await self.session.execute(
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(balance=self.model.balance + amount)
        )

    # ------------------------------------------------------------ выборки
    async def list_subscribed(self) -> Sequence[UserOrm]:
        stmt = select(self.model).where(self.model.banned.is_(False), self.model.email.is_not(None))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_expiring(self, before_ms: int) -> Sequence[UserOrm]:
        stmt = select(self.model).where(
            self.model.expiry_at > 0,
            self.model.expiry_at <= before_ms,
            self.model.banned.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_all(self) -> int:
        return int(await self.session.scalar(select(func.count()).select_from(self.model)) or 0)

    async def count_active(self) -> int:
        stmt = select(func.count()).select_from(self.model).where(
            self.model.is_active.is_(True), self.model.banned.is_(False)
        )
        return int(await self.session.scalar(stmt) or 0)

    async def count_banned(self) -> int:
        stmt = select(func.count()).select_from(self.model).where(self.model.banned.is_(True))
        return int(await self.session.scalar(stmt) or 0)
