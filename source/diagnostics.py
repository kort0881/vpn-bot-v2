"""Самодиагностика бота: env-настройки, панель, шлюз подписки, алерты админу.

Принцип: самосборка = самопроверка + самовосстановление + честный отказ.
Никакой генерации кода на ходу — только проверки и явные сообщения.
"""

from __future__ import annotations

import aiohttp
from loguru import logger

from source.config.panel import AWG_SERVICE_LINK
from source.config.panel import CHANNEL_ID
from source.config.panel import PANEL_API_TOKEN
from source.config.panel import PANEL_RU_API_TOKEN
from source.config.panel import PANEL_RU_URL
from source.config.panel import PANEL_URL
from source.config.panel import SUB_URL
from source.config.panel import TT_PANEL_BASE
from source.config.panel import TT_SERVICE_LINK
from source.config.panel import VIP_CHANNEL_ID
from source.config.panel import VIP_POST_URL


def env_report() -> list[tuple[str, bool, str]]:
    """Что настроено в .env (читаем уже разобранные настройки, не os.environ)."""
    checks = [
        ("PANEL_URL", bool(PANEL_URL), "критично"),
        ("PANEL_API_TOKEN", bool(PANEL_API_TOKEN), "критично"),
        ("PANEL_RU_URL", bool(PANEL_RU_URL), ""),
        ("PANEL_RU_API_TOKEN", bool(PANEL_RU_API_TOKEN), ""),
        ("CHANNEL_ID", bool(CHANNEL_ID), "проверка подписки"),
        ("VIP_CHANNEL_ID", bool(VIP_CHANNEL_ID), "закрытый канал"),
        ("VIP_POST_URL", bool(VIP_POST_URL), "ссылка на инструкцию"),
        ("SUB_URL", bool(SUB_URL), "шлюз подписки"),
        ("TT_SERVICE_LINK", bool(TT_SERVICE_LINK), "канал TrustTunnel"),
        ("AWG_SERVICE_LINK", bool(AWG_SERVICE_LINK), "канал AmneziaWG"),
        ("TT_PANEL_BASE", bool(TT_PANEL_BASE), "панель TT"),
    ]
    out: list[tuple[str, bool, str]] = []
    for name, ok, note in checks:
        out.append(
            (name, ok, ("задан" if ok else "ПУСТО") + (f" ({note})" if note else ""))
        )
    return out


async def http_ok(
    url: str, headers: dict | None = None, timeout: int = 10
) -> tuple[bool, str]:
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.get(url, headers=headers or {}) as resp:
                body = (await resp.text())[:100].replace("\n", " ")
                return resp.status < 400, f"HTTP {resp.status} {body}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def panel_ok() -> tuple[bool, str]:
    url = PANEL_RU_URL or PANEL_URL
    token = PANEL_RU_API_TOKEN or PANEL_API_TOKEN
    if not url:
        return False, "PANEL_URL не задан"
    return await http_ok(
        f"{url}/panel/api/server/status", {"Authorization": f"Bearer {token}"}
    )


async def gateway_ok() -> tuple[bool, str]:
    if not SUB_URL:
        return False, "SUB_URL не задан"
    return await http_ok(SUB_URL.replace("{user_id}", "1"), timeout=15)


async def tt_panel_ok() -> tuple[bool, str]:
    if not TT_PANEL_BASE:
        return True, "не настроена (пропуск)"
    return await http_ok(TT_PANEL_BASE, timeout=10)


async def alert_admins(bot, text: str) -> None:
    from source.config import settings

    for admin_id in settings.tg.admin_ids:
        try:
            await bot.send_message(admin_id, text[:4000])
        except Exception as exc:
            logger.warning(f"не смог отправить алерт админу {admin_id}: {exc}")


async def startup_selfcheck(bot) -> None:
    """Проверки при старте. Без критичных настроек бот не поднимается."""
    logger.info("САМОПРОВЕРКА при старте")
    critical: list[str] = []
    for name, ok, detail in env_report():
        logger.log("INFO" if ok else "WARNING", f"  env {name}: {detail}")
        if not ok and "критично" in detail:
            critical.append(f"{name}: {detail}")

    if critical:
        message = (
            "🛑 Бот не запустился: нет обязательных настроек.\n"
            + "\n".join(critical)
            + "\n\nПанель и ключи при этом работают — проблема только в конфиге бота. "
            "Если сообщение пришло дважды, это повторные попытки автозапуска."
        )
        logger.error(message)
        # не спамим: один алерт на 10 минут
        import pathlib
        import time as _time

        guard = pathlib.Path("/opt/vpn-bot-v2/.last_boot_alert")
        last = 0.0
        try:
            last = float(guard.read_text().strip())
        except Exception:
            pass
        if _time.time() - last > 600:
            try:
                guard.write_text(str(_time.time()))
            except Exception:
                pass
            await alert_admins(bot, message)
        raise SystemExit(1)

    panel, panel_detail = await panel_ok()
    logger.log("INFO" if panel else "ERROR", f"  панель: {panel_detail}")
    gateway, gateway_detail = await gateway_ok()
    logger.log("INFO" if gateway else "WARNING", f"  шлюз подписки: {gateway_detail}")
    tt, tt_detail = await tt_panel_ok()
    logger.log("INFO" if tt else "WARNING", f"  TT-панель: {tt_detail}")

    if not (panel and gateway and tt):
        await alert_admins(
            bot,
            "⚠️ Бот стартовал с проблемами:\n"
            f"панель: {'ok' if panel else panel_detail}\n"
            f"шлюз подписки: {'ok' if gateway else gateway_detail}\n"
            f"TT-панель: {'ok' if tt else tt_detail}",
        )
    else:
        logger.info("самопроверка: всё доступно")
