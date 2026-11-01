"""/selfcheck — ручная самодиагностика бота (только админ)."""

import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.config import settings
from source.diagnostics import env_report
from source.diagnostics import gateway_ok
from source.diagnostics import panel_ok
from source.diagnostics import tt_panel_ok
from source.services import AccessService

selfcheck_router = Router(name="admin-selfcheck")


@selfcheck_router.message(Command("selfcheck"))
@aiogram_inject
async def selfcheck(message: Message, access: FromDishka[AccessService]) -> None:
    if message.from_user.id not in set(settings.tg.admin_ids):
        return

    lines = ["🩺 <b>Самопроверка</b>", ""]

    bad_env = [name for name, ok, _ in env_report() if not ok]
    lines.append(
        "✅ env: обязательное на месте"
        if not bad_env
        else "⚠️ env пусто: " + ", ".join(bad_env)
    )

    try:
        issued = await access.keys_issued()
        lines.append(f"✅ БД: отвечает (выдано ключей: {issued})")
    except Exception as exc:
        lines.append(f"❌ БД: {type(exc).__name__}: {exc}")

    ok, detail = await panel_ok()
    lines.append(f"{'✅' if ok else '❌'} панель: {detail}")

    ok, detail = await gateway_ok()
    lines.append(f"{'✅' if ok else '❌'} шлюз подписки: {detail}")

    ok, detail = await tt_panel_ok()
    lines.append(f"{'✅' if ok else '⚠️'} TT-панель: {detail}")

    try:
        stamp = float(open("/opt/vpn-bot-v2/.last_restart").read().strip())
        lines.append(
            f"ℹ️ авто-перезапуск: {time.strftime('%d.%m %H:%M', time.localtime(stamp))}"
        )
    except Exception:
        lines.append("ℹ️ авто-перезапусков не было")

    await message.answer("\n".join(lines))
