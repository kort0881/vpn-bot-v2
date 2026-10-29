"""Фоновое продление подписок и отключение отписавшихся.

Перенесено из renewal_loop (старый main.py):
  * подписан и до конца < RENEW_THRESHOLD_DAYS -> продлить на EXPIRE_DAYS;
  * не подписан -> выключить клиента в панели, пометить в БД, отправить текст.
"""

from __future__ import annotations

import asyncio
import time

from aiogram import Bot
from loguru import logger

from source.config.panel import CHANNEL_ID
from source.config.panel import EXPIRE_MS
from source.config.panel import RENEW_INTERVAL_MINUTES
from source.config.panel import RENEW_THRESHOLD_DAYS
from source.config.panel import RESUBSCRIBE_BAN_DAYS
from source.services import AccessService
from source.services import VpnPanelService
from source.utils import I18n
from source.utils.subscription import is_subscribed

THRESHOLD_MS = RENEW_THRESHOLD_DAYS * 24 * 3600 * 1000

# Отключаем не с первого «не подписан», а со второго подтверждения подряд:
# разовый сбой get_chat_member не должен лишать человека доступа.
UNSUB_STRIKES_REQUIRED = 2
_unsub_strikes: dict[int, int] = {}


async def _tick(bot: Bot, access: AccessService, vpn: VpnPanelService, i18n: I18n) -> None:
    users = await access.renewal_users()
    now = int(time.time() * 1000)
    renewed = disabled = 0

    for user in users:
        try:
            subscribed = await is_subscribed(bot, user.user_id, CHANNEL_ID)
            expiry = int(user.expiry_at or 0)

            if subscribed:
                _unsub_strikes.pop(user.user_id, None)
                if expiry - now < THRESHOLD_MS:
                    new_expiry = max(expiry, now) + EXPIRE_MS
                    ok = await vpn.panel.update_client(
                        user.email, user.client_uuid, enable=True, expiry_time=new_expiry
                    )
                    if ok:
                        await access.set_expiry(user.user_id, new_expiry)
                        renewed += 1
                        logger.info(f"продлён {user.email} -> {new_expiry}")
            else:
                strikes = _unsub_strikes.get(user.user_id, 0) + 1
                _unsub_strikes[user.user_id] = strikes
                if strikes < UNSUB_STRIKES_REQUIRED:
                    logger.info(
                        f"{user.email}: нет подписки ({strikes}/{UNSUB_STRIKES_REQUIRED}), не отключаю"
                    )
                    continue
                ok = await vpn.panel.update_client(user.email, user.client_uuid, enable=False)
                if ok:
                    _unsub_strikes.pop(user.user_id, None)
                    await access.mark_unsubscribed(user.user_id)
                    disabled += 1
                    logger.info(f"отключён {user.email} (нет подписки)")
                    try:
                        await bot.send_message(
                            user.user_id,
                            await i18n(user.user_id, "kick-unsubscribed", days=RESUBSCRIBE_BAN_DAYS),
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(f"kick -> {user.user_id}: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"продление {getattr(user, 'email', '?')}: {exc}")

    if renewed or disabled:
        logger.info(f"цикл продления: продлено {renewed}, отключено {disabled}")


async def renewal_loop(bot: Bot, container) -> None:
    """Каждый тик открывает свой REQUEST-scope: сервисы живут ровно один проход."""
    from dishka import Scope

    logger.info(
        f"цикл продления запущен (интервал {RENEW_INTERVAL_MINUTES} мин, "
        f"порог {RENEW_THRESHOLD_DAYS} дн)"
    )
    while True:
        try:
            async with container(scope=Scope.REQUEST) as request:
                access = await request.get(AccessService)
                vpn = await request.get(VpnPanelService)
                i18n = await request.get(I18n)
                await _tick(bot, access, vpn, i18n)
        except asyncio.CancelledError:
            logger.info("цикл продления остановлен")
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error(f"цикл продления: {exc}")
        await asyncio.sleep(RENEW_INTERVAL_MINUTES * 60)
