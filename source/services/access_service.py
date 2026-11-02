"""Доменный сервис доступа: связывает БД (Postgres) и панель (3x-UI).

Здесь вся логика «есть ли у человека ключ, выдать/обновить/забанить»,
чтобы хендлеры были тонкими и не знали ни про панель, ни про SQL.
"""

from __future__ import annotations

import time
from datetime import datetime

from loguru import logger

from source.config.panel import LIMIT_IP
from source.config.panel import RESUBSCRIBE_BAN_DAYS
from source.database import AbstractUnitOfWork
from source.database.models import UserOrm
from source.services.base import BaseService
from source.services.panel_client import PanelClient
from source.services.vpn_service import VpnPanelService

GB = 1024**3


class AccessService(BaseService):
    def __init__(self, uow: AbstractUnitOfWork, vpn: VpnPanelService) -> None:
        self._uow = uow
        self.vpn = vpn

    # ------------------------------------------------------------------ профиль
    async def ensure_user(self, user_id: int, username: str = "") -> UserOrm:
        async with self._uow:
            user = await self._uow.users.upsert_user(user_id, {"username": username or ""})
            if username:
                await self._uow.users.set_username(user_id, username)
            return user

    async def get_user(self, user_id: int) -> UserOrm | None:
        async with self._uow:
            return await self._uow.users.get(user_id)

    async def is_banned(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        return bool(user and user.banned)

    def ban_until_text(self, user: UserOrm | None) -> tuple[bool, str]:
        """Вернуть (показывать_срок, срок) для текста бана."""
        if not user or not user.unsubscribed_at:
            return False, ""
        left_ms = user.unsubscribed_at + RESUBSCRIBE_BAN_DAYS * 86400 * 1000 - time.time() * 1000
        days = int(left_ms / (86400 * 1000)) + 1
        if days <= 0:
            return False, ""
        return True, ("1 день" if days == 1 else f"{days} дн.")

    # ------------------------------------------------------------------ ключ
    @staticmethod
    def has_active_key(user: UserOrm | None) -> bool:
        if not user or not user.email or not user.vless_link:
            return False
        if not user.is_active or user.banned:
            return False
        if user.expiry_at and user.expiry_at < time.time() * 1000:
            return False
        return True

    async def issue_key(self, user_id: int, username: str = "") -> tuple[UserOrm, PanelClient]:
        user = await self.ensure_user(user_id, username)
        client = await self.vpn.issue_key(user_id, username)
        async with self._uow:
            await self._uow.users.save_key(
                user_id,
                email=client.email,
                client_uuid=client.uuid,
                vless_link=(client.links or [""])[0],
                links=list(client.links or []),
                total_bytes=int(getattr(client, "total_gb", 0) or user.total_bytes or 0),
                expiry_at=int(getattr(client, "expiry_time", 0) or user.expiry_at or 0),
            )
        logger.info(f"ключ выдан: {user_id} ({client.email}), ссылок: {len(client.links or [])}")
        return await self.get_user(user_id) or user, client

    async def refresh_key(self, user_id: int) -> dict:
        user = await self.get_user(user_id)
        if not user or not user.email:
            return {"ok": False, "reason": "нет ключа"}
        try:
            result = await self.vpn.refresh_key(user.email)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"refresh_key {user.email}: {exc}")
            return {"ok": False, "reason": f"error: {exc}"}
        expiry = int(result.get("expiry") or 0)
        if result.get("ok") and expiry:
            async with self._uow:
                await self._uow.users.update(user_id, {"expiry_at": expiry, "is_active": True})
        return result

    async def links_of(self, user: UserOrm | None) -> list[str]:
        if not user:
            return []
        links = list(user.links or [])
        if not links and user.vless_link:
            links = [user.vless_link]
        return links

    @staticmethod
    def stats_text(user: UserOrm) -> dict:
        used_gb = float(user.used_bytes or 0) / GB
        total_gb = float(user.total_bytes or 0) / GB
        expiry = "—"
        if user.expiry_at:
            expiry = datetime.fromtimestamp(user.expiry_at / 1000).strftime("%d.%m.%Y")
        return {"used": f"{used_gb:.1f}", "total": f"{total_gb:.0f}", "expiry": expiry, "limit": LIMIT_IP}

    async def issue_xhttp(self, user_id: int) -> dict | None:
        return await self.vpn.issue_xhttp(user_id)

    async def issue_sel(self, user_id: int) -> dict | None:
        """Ключ канала Selectel (3 ТБ) — обёртка над VpnPanelService.issue_sel."""
        return await self.vpn.issue_sel(user_id)

    async def save_poll_answer(
        self,
        poll_id: str,
        telegram_id: int,
        username: str = "",
        full_name: str = "",
        option_ids: str = "[]",
    ) -> None:
        """Записать голос в опросе канала (таблица poll_answers)."""
        async with self._uow:
            await self._uow.polls.add(
                {
                    "poll_id": (poll_id or "")[:64],
                    "telegram_id": telegram_id,
                    "username": (username or "")[:128],
                    "full_name": (full_name or "")[:256],
                    "option_ids": option_ids,
                }
            )

    # ------------------------------------------------------------------ счётчики
    async def keys_issued(self) -> int:
        async with self._uow:
            return await self._uow.stats.get_value("keys_issued")

    async def incr_keys(self) -> int:
        async with self._uow:
            return await self._uow.stats.incr("keys_issued", 1)

    # ------------------------------------------------------------------ бан/подписка
    async def ban(self, user_id: int, reason: str = "") -> None:
        async with self._uow:
            await self._uow.users.set_banned(user_id, True, reason, int(time.time() * 1000))

    async def unban(self, user_id: int) -> None:
        async with self._uow:
            await self._uow.users.set_banned(user_id, False, "", 0)

    async def mark_unsubscribed(self, user_id: int) -> None:
        async with self._uow:
            await self._uow.users.set_unsubscribed(user_id, int(time.time() * 1000))

    # ------------------------------------------------------------------ поддержка/админка
    async def save_support_message(
        self, telegram_id: int, username: str, full_name: str, text: str, created_at: int
    ) -> None:
        async with self._uow:
            await self._uow.support.add(
                {
                    "telegram_id": telegram_id,
                    "username": username[:128],
                    "full_name": full_name[:256],
                    "text": text,
                    "created_at": created_at,
                    "status": "new",
                }
            )

    async def new_support_messages(self, limit: int = 10) -> list[dict]:
        async with self._uow:
            rows = await self._uow.support.list_new(limit)
            return [
                {
                    "id": row.id,
                    "telegram_id": row.telegram_id,
                    "username": row.username,
                    "text": row.text,
                }
                for row in rows
            ]

    async def subscribed_ids(self) -> list[int]:
        async with self._uow:
            users = await self._uow.users.list_subscribed()
            return [int(u.user_id) for u in users]

    async def admin_stats(self) -> dict:
        async with self._uow:
            users = await self._uow.users.count_all()
            active = await self._uow.users.count_active()
            banned = await self._uow.users.count_banned()
            keys = await self._uow.stats.get_value("keys_issued")
            payments = await self._uow.payments.list_recent(1000)
            support_new = len(await self._uow.support.list_new(100))
            paid_sum = await self._uow.payments.total_confirmed()
        return {
            "users": users,
            "active": active,
            "banned": banned,
            "keys": keys,
            "payments": len(payments),
            "paid_sum": paid_sum,
            "support_new": support_new,
        }

    # ------------------------------------------------------------------ продление
    async def renewal_users(self) -> list[UserOrm]:
        async with self._uow:
            return list(await self._uow.users.list_subscribed())

    async def set_expiry(self, user_id: int, expiry_at: int) -> None:
        async with self._uow:
            await self._uow.users.update(user_id, {"expiry_at": expiry_at, "is_active": True})
