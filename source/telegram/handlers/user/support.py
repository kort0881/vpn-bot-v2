"""Обращения в поддержку, шум и капча.

Старый бот: is_noise() отбрасывал мусор, support_fallback сохранял текст в
support_messages и слал копию админу, handle_captcha проверял пять цифр.
"""

import asyncio
import html
import time

from aiogram import F
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject
from loguru import logger

from source.config import settings
from source.services import AccessService
from source.services import smart_reply
from source.services.autoreply import match as autoreply_match
from source.telegram.handlers.user.keys import send_key
from source.telegram.states import CaptchaSG
from source.utils import I18n

user_support_router = Router(name=__name__)

NOISE = {
    "/start",
    "/vpn",
    "/menu",
    "/help",
    "/donate",
    "привет",
    "здравствуйте",
    "спасибо",
    "ок",
    "ok",
    "hello",
    "hi",
    "+",
    "?",
}


def is_noise(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return True
    if value in NOISE:
        return True
    return len(value) < 3


@user_support_router.message(StateFilter(CaptchaSG.waiting_captcha), F.text)
@aiogram_inject
async def handle_captcha(
    message: Message,
    state: FSMContext,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    data = await state.get_data()
    expected = str(data.get("captcha", ""))
    answer = (message.text or "").strip()
    if expected and answer == expected:
        await state.clear()
        await send_key(
            message, message.from_user.id, access, i18n, state, skip_captcha=True
        )
        return
    await message.answer(await i18n(message.from_user.id, "captcha-wrong"))


@user_support_router.message(F.text & ~F.text.startswith("/"))
@aiogram_inject
async def support_fallback(
    message: Message, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    user = message.from_user
    text = message.text or ""
    if is_noise(text):
        await message.answer(await i18n(user.id, "any-message"))
        return

    # умный ответ через ИИ (если есть ключи): сначала он, потом локальные правила
    try:
        profile = await access.get_user(user.id)
        facts = smart_reply.build_facts(
            {
                "is_active": bool(profile and profile.is_active),
                "expiry_at": int(profile.expiry_at or 0) if profile else 0,
                "used_bytes": float(profile.used_bytes or 0) if profile else 0,
                "total_bytes": int(profile.total_bytes or 0) if profile else 0,
                "banned": bool(profile and profile.banned),
            }
            if profile
            else None
        )
        smart = await asyncio.to_thread(smart_reply.answer, text, facts)
        if smart:
            await message.answer(smart)
            logger.info(f"smart_reply -> {user.id}")
            return
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"smart_reply упал, отдаю автоответчик: {exc}")

    # автоответ на типовой вопрос (0 токенов, локальный матчинг)
    rule = autoreply_match(user.id, text)
    if rule:
        if rule == "howto":
            await message.answer(
                await i18n(user.id, "help-title")
                + "\n\n"
                + await i18n(user.id, "help-short")
            )
        elif rule == "link":
            await message.answer(await i18n(user.id, "autoreply-link"))
        else:
            await message.answer(await i18n(user.id, f"autoreply-{rule}"))
        logger.info(f"autoreply {rule} -> {user.id}")
        return

    await access.save_support_message(
        telegram_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        text=text,
        created_at=int(time.time() * 1000),
    )
    await message.answer(await i18n(user.id, "support-saved"))

    for admin_id in settings.tg.admin_ids or []:
        try:
            await message.bot.send_message(
                admin_id,
                "🆘 <b>Обращение</b>\n"
                f"от: {html.escape(user.full_name or '')} (@{user.username or '—'}, "
                f"<code>{user.id}</code>)\n\n{html.escape(text)}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"support forward -> {admin_id}: {exc}")
