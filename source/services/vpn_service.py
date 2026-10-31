"""Сервис выдачи VPN-ключей поверх 3x-UI.

Является фасадом над низкоуровневым `PanelSession` (source/services/panel_client.py):
хендлеры работают только с этим сервисом и не знают про HTTP-детали панели.

Каналы:
  * основной каскад (RU-вход 2087/443) — массовые ключи;
  * VIP (инбаунд из VIP_INBOUND_ID) — подписчики закрытого канала;
  * XHTTP через nginx (self-steal, инбаунд XHTTP_INBOUND_ID) — для операторов,
    где основной канал режут;
  * Selectel (SEL_*) и TrustTunnel (TT_*) — дополнительные каналы.
"""

from __future__ import annotations

import logging
import urllib.parse
import uuid as uuid_lib
from typing import Optional

from source.config.panel import (
    EXPIRE_MS,
    LIMIT_IP,
    SEL_ENABLED,
    TOTAL_BYTES,
    VIP_TOTAL_BYTES,
    XHTTP_ENABLED,
    XHTTP_HOST,
    XHTTP_INBOUND_ID,
    XHTTP_MODE,
    XHTTP_PATH,
    XHTTP_PORT,
    XHTTP_SNI,
    XHTTP_TOTAL_BYTES,
)
from source.services.base import BaseService
from source.services.panel_client import PanelClient
from source.services.panel_client import PanelSession

logger = logging.getLogger(__name__)


class VpnPanelService(BaseService):
    """Высокоуровневые операции с панелью: выдача, продление, трафик, VIP, XHTTP."""

    def __init__(self, panel: PanelSession) -> None:
        self.panel = panel

    # ------------------------------------------------------------------ массовый канал
    async def issue_key(self, tg_id: int, username: str = "") -> PanelClient:
        """Создать (или обновить существующего) клиента во всех инбаундах входа."""
        return await self.panel.add_client(tg_id, username)

    async def refresh_key(self, email: str) -> dict:
        return await self.panel.refresh_client(email)

    async def delete_key(self, email: str) -> None:
        await self.panel.delete_client(email)

    async def traffic_map(self) -> dict:
        return await self.panel.get_traffic_map()

    async def client_traffic(self, email: str) -> dict | None:
        return await self.panel.get_client_traffic(email)

    # ------------------------------------------------------------------ VIP-канал
    async def issue_vip(self, tg_id: int) -> dict | None:
        return await self.panel.add_vip_client(tg_id)

    async def refresh_vip(self, tg_id: int) -> str | None:
        return await self.panel.refresh_vip_link(tg_id)

    async def set_vip_enabled(self, tg_id: int, enable: bool) -> bool:
        return await self.panel.set_vip_enabled(tg_id, enable)

    async def vip_traffic(self, tg_id: int) -> float | None:
        return await self.panel.get_vip_traffic(tg_id)

    # ------------------------------------------------------------------ Selectel / TT
    async def issue_sel(self, tg_id: int) -> dict | None:
        if not SEL_ENABLED:
            return None
        return await self.panel.add_sel_client(tg_id)

    async def issue_cascade(self, tg_id: int, username: str = "") -> PanelClient | None:
        return await self.panel.add_cascade_client(tg_id, username)

    # ------------------------------------------------------------------ XHTTP (self-steal)
    async def issue_xhttp(self, tg_id: int) -> dict | None:
        """Выдать ключ XHTTP через nginx на 443 (канал для белых списков).

        Создаёт клиента только в XHTTP-инбаунде и возвращает готовую ссылку.
        """
        if not XHTTP_ENABLED:
            logger.warning("XHTTP-канал выключен (XHTTP_ENABLED=0)")
            return None

        email = f"tg_{tg_id}"
        client_uuid = str(uuid_lib.uuid4())
        payload = {
            "id": XHTTP_INBOUND_ID,
            "settings": {
                "clients": [
                    {
                        "id": client_uuid,
                        "email": email,
                        "limitIp": LIMIT_IP,
                        "totalGB": XHTTP_TOTAL_BYTES,
                        "expiryTime": int(__import__("time").time() * 1000) + EXPIRE_MS,
                        "enable": True,
                        "flow": "",
                        "tgId": tg_id,
                        "subId": "",
                    }
                ]
            },
        }
        try:
            await self.panel._request(  # noqa: SLF001 — тонкая обёртка над API панели
                "POST", "/panel/api/inbounds/addClient", json=payload
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("XHTTP: не удалось создать клиента %s: %s", email, exc)
            return None

        link = self.build_xhttp_link(client_uuid, email)
        return {"email": email, "uuid": client_uuid, "link": link}

    @staticmethod
    def build_xhttp_link(client_uuid: str, remark: str = "") -> str:
        query = {
            "type": "xhttp",
            "security": "tls",
            "sni": XHTTP_SNI,
            "host": XHTTP_HOST,
            "path": XHTTP_PATH,
            "mode": XHTTP_MODE,
            "fp": "chrome",
            "alpn": "h2,http/1.1",
        }
        tail = urllib.parse.quote(remark or "XHTTP", safe="")
        return (
            f"vless://{client_uuid}@{XHTTP_HOST}:{XHTTP_PORT}?"
            + urllib.parse.urlencode(query, quote_via=urllib.parse.quote)
            + f"#%D0%91%D0%A1%20{tail}"
        )

    # ------------------------------------------------------------------ прочее
    async def close(self) -> None:
        await self.panel.close()
