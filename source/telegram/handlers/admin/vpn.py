"""Админские команды: статистика, рассылка, бан, очередь обращений."""

from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.filters import Command
from aiogram.filters import CommandObject
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject
from loguru import logger

from source.config import settings
from source.services import AccessService

admin_vpn_router = Router(name=__name__)


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(settings.tg.admin_ids) and message.from_user.id in settings.tg.admin_ids


@admin_vpn_router.message(Command("stats"), IsAdmin())
@aiogram_inject
async def stats(message: Message, access: FromDishka[AccessService]) -> None:
    data = await access.admin_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 всего пользователей: <b>{data['users']}</b>\n"
        f"✅ активных: <b>{data['active']}</b>\n"
        f"🚫 забаненных: <b>{data['banned']}</b>\n"
        f"🔑 выдано ключей: <b>{data['keys']}</b>\n"
        f"💳 платежей: <b>{data['payments']}</b> на <b>{data['paid_sum']}</b> ₽\n"
        f"🆘 новых обращений: <b>{data['support_new']}</b>"
    )
    await message.answer(text)


@admin_vpn_router.message(Command("broadcast"), IsAdmin())
@aiogram_inject
async def broadcast(message: Message, command: CommandObject, access: FromDishka[AccessService]) -> None:
    text = (command.args or "").strip()
    if not text:
        await message.answer("Использование: /broadcast текст сообщения")
        return
    user_ids = await access.subscribed_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logger.debug(f"broadcast -> {uid}: {exc}")
    await message.answer(f"📨 Рассылка завершена: доставлено {sent}, ошибок {failed}")


@admin_vpn_router.message(Command("ban"), IsAdmin())
@aiogram_inject
async def ban(message: Message, command: CommandObject, access: FromDishka[AccessService]) -> None:
    parts = (command.args or "").split(maxsplit=1)
    if not parts or not parts[0].isdigit():
        await message.answer("Использование: /ban <telegram_id> [причина]")
        return
    target = int(parts[0])
    reason = parts[1] if len(parts) > 1 else ""
    await access.ban(target, reason)
    await message.answer(f"🚫 Забанен {target}" + (f": {reason}" if reason else ""))


@admin_vpn_router.message(Command("unban"), IsAdmin())
@aiogram_inject
async def unban(message: Message, command: CommandObject, access: FromDishka[AccessService]) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Использование: /unban <telegram_id>")
        return
    target = int(arg)
    await access.unban(target)
    await message.answer(f"✅ Разбанен {target}")


@admin_vpn_router.message(Command("support"), IsAdmin())
@aiogram_inject
async def support_queue(message: Message, access: FromDishka[AccessService]) -> None:
    items = await access.new_support_messages(limit=10)
    if not items:
        await message.answer("🆘 Новых обращений нет")
        return
    lines = ["🆘 <b>Новые обращения</b>", ""]
    for item in items:
        lines.append(
            f"#{item['id']} · {item['telegram_id']} · "
            f"{item['username'] or '—'}\n{str(item['text'])[:200]}"
        )
    await message.answer("\n\n".join(lines))
