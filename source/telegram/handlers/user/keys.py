import random

from aiogram import F
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import CopyTextButton
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject
from loguru import logger

from source.config.panel import AWG_APP_URL
from source.config.panel import AWG_SERVICE_LINK
from source.config.panel import CHANNEL_ID
from source.config.panel import TT_APP_URL
from source.config.panel import FALLBACK_SUB_URL
from source.config.panel import VIP_POST_URL
from source.config.panel import TT_SERVICE_LINK
from source.config.panel import DONATE_URL
from source.config.panel import SUB_URL
from source.config.panel import VIP_INVITE_URL
from source.services import AccessService
from source.telegram.states import CaptchaSG
from source.telegram.handlers.user.commands import banned_text
from source.telegram.keyboards.vpn import back_to_menu_kb
from source.telegram.keyboards.vpn import copy_kb
from source.telegram.keyboards.vpn import donate_kb
from source.telegram.keyboards.vpn import help_kb
from source.telegram.keyboards.vpn import keys_kb
from source.telegram.keyboards.vpn import main_menu_kb
from source.telegram.keyboards.vpn import my_key_empty_kb
from source.telegram.keyboards.vpn import trouble_kb
from source.telegram.navigation import render
from source.utils import I18n
from source.utils.subscription import is_subscribed

user_keys_router = Router(name=__name__)


def subscription_url(user_id: int) -> str:
    return SUB_URL.format(user_id=user_id)


async def build_keys_text(access: AccessService, i18n: I18n, user) -> str:
    stats = AccessService.stats_text(user)
    parts = [
        await i18n(user.user_id, "subscription-title"),
        f"<code>{subscription_url(user.user_id)}</code>",
        await i18n(user.user_id, "subscription-routes"),
        await i18n(user.user_id, "keys-hint"),
        await i18n(user.user_id, "keys-stats", **stats),
        await i18n(user.user_id, "keys-tail"),
    ]
    return "\n\n".join(parts)


async def send_key(
    message: Message,
    user_id: int,
    access: AccessService,
    i18n: I18n,
    state: FSMContext | None = None,
    skip_captcha: bool = False,
) -> None:
    """Выдать ключ (или показать существующий). Новым — с капчей."""
    username = getattr(message.from_user, "username", "") or ""
    profile = await access.ensure_user(user_id, username)

    if profile.banned:
        await message.answer(await banned_text(access, i18n, user_id, profile))
        return

    if not await is_subscribed(message.bot, user_id, CHANNEL_ID):
        await message.answer(await i18n(user_id, "subscription-required"))
        return

    if state is not None and not skip_captcha and not access.has_active_key(profile):
        code = "".join(random.choices("0123456789", k=5))
        await state.set_state(CaptchaSG.waiting_captcha)
        await state.update_data(captcha=code)
        await message.answer(f"{await i18n(user_id, 'captcha-ask')}\n\n<b>{code}</b>")
        return

    await message.answer(await i18n(user_id, "generation"))
    try:
        if access.has_active_key(profile):
            user = profile
        else:
            user, _client = await access.issue_key(user_id, username)
            await access.incr_keys()
    except Exception as exc:
        logger.exception(f"send_key {user_id}: {exc}")
        if FALLBACK_SUB_URL:
            logger.warning(
                f"send_key {user_id}: панель недоступна, отдаю временную ссылку"
            )
            await message.answer(
                await i18n(user_id, "fallback-note")
                + f"\n\n<code>{FALLBACK_SUB_URL}</code>"
            )
            return
        await message.answer(await i18n(user_id, "error", error=str(exc)[:200]))
        return

    await message.answer(
        await build_keys_text(access, i18n, user),
        reply_markup=await keys_kb(i18n, user_id),
    )


@user_keys_router.callback_query(F.data == "get_key")
@aiogram_inject
async def get_key(
    callback: CallbackQuery,
    state: FSMContext,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    await callback.answer()
    await send_key(callback.message, callback.from_user.id, access, i18n, state)


@user_keys_router.callback_query(F.data == "my_key")
@aiogram_inject
async def my_key(
    callback: CallbackQuery, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    user = await access.get_user(user_id)
    if not access.has_active_key(user):
        await callback.message.edit_text(
            await i18n(user_id, "my-key-empty"),
            reply_markup=await my_key_empty_kb(i18n, user_id),
        )
        return
    await callback.message.edit_text(
        await build_keys_text(access, i18n, user),
        reply_markup=await keys_kb(i18n, user_id),
    )


@user_keys_router.callback_query(F.data == "refresh_key")
@aiogram_inject
async def refresh_key(
    callback: CallbackQuery, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    user_id = callback.from_user.id
    user = await access.get_user(user_id)
    if not access.has_active_key(user):
        await callback.answer(await i18n(user_id, "refresh-no-access"), show_alert=True)
        return
    await callback.answer(await i18n(user_id, "refresh-progress"))

    result = await access.refresh_key(user_id)
    from datetime import datetime

    if result.get("ok"):
        when = datetime.now().strftime("%H:%M:%S")
        text = await i18n(
            user_id, "refresh-ok", time=when, channels=result.get("panel", "RU")
        )
        expiry = int(result.get("expiry") or 0)
        if expiry:
            date = datetime.fromtimestamp(expiry / 1000).strftime("%d.%m.%Y")
            text += "\n" + await i18n(user_id, "refresh-ok-expiry", date=date)
        await callback.message.answer(text)
    else:
        await callback.message.answer(
            await i18n(user_id, "refresh-fail", detail=str(result.get("reason"))[:120])
        )


@user_keys_router.callback_query(F.data == "copy_sub")
@aiogram_inject
async def copy_sub(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    await render(
        callback,
        await i18n(user_id, "copy-sub-title")
        + f"\n\n<code>{subscription_url(user_id)}</code>",
        await copy_kb(i18n, user_id, back_to="my_key"),
    )


@user_keys_router.callback_query(F.data == "copy_happ")
@aiogram_inject
async def copy_happ(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    url = subscription_url(user_id) + "?f=happ"
    await render(
        callback,
        await i18n(user_id, "copy-happ") + f"\n\n<code>{url}</code>",
        await copy_kb(i18n, user_id, back_to="my_key"),
    )


@user_keys_router.callback_query(F.data == "xhttp_key")
@aiogram_inject
async def xhttp_key(
    callback: CallbackQuery, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    user_id = callback.from_user.id
    await callback.answer(await i18n(user_id, "generation"))
    result = await access.issue_xhttp(user_id)
    if not result:
        await callback.message.answer(await i18n(user_id, "xhttp-disabled"))
        return
    await render(
        callback,
        await i18n(user_id, "xhttp-title")
        + "\n\n"
        + await i18n(user_id, "xhttp-issued")
        + f"\n\n<code>{result['link']}</code>",
        await keys_kb(i18n, user_id),
    )


@user_keys_router.callback_query(F.data == "main_menu")
@aiogram_inject
async def main_menu(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    await render(
        callback,
        await i18n(user_id, "main-menu"),
        await main_menu_kb(i18n, user_id, DONATE_URL),
    )


@user_keys_router.callback_query(F.data == "help")
@aiogram_inject
async def help_cb(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    text = await i18n(user_id, "help-title")
    if VIP_INVITE_URL:
        text += "\n" + await i18n(user_id, "help-channel", link=VIP_INVITE_URL)
    text += "\n\n" + await i18n(user_id, "help-short")
    if VIP_POST_URL:
        text += (
            "\n\n" + await i18n(user_id, "help-post") + f"\n<code>{VIP_POST_URL}</code>"
        )
    text += "\n\n" + await i18n(user_id, "help-warning")
    await render(
        callback,
        text,
        await help_kb(
            i18n, user_id, VIP_INVITE_URL, back_to="main_menu", post_url=VIP_POST_URL
        ),
    )


@user_keys_router.callback_query(F.data == "trouble_help")
@aiogram_inject
async def trouble_help(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    text = "\n\n".join(
        [
            await i18n(user_id, "trouble-title"),
            await i18n(user_id, "trouble-steps"),
            await i18n(user_id, "trouble-tail"),
        ]
    )
    await render(callback, text, await trouble_kb(i18n, user_id, back_to="help"))


@user_keys_router.callback_query(F.data == "donate")
@aiogram_inject
async def donate_cb(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer()
    user_id = callback.from_user.id
    await render(
        callback,
        await i18n(user_id, "donate-title"),
        await donate_kb(i18n, user_id, DONATE_URL, back_to="main_menu"),
    )


@user_keys_router.callback_query(F.data == "check_sub")
@aiogram_inject
async def check_sub(
    callback: CallbackQuery,
    state: FSMContext,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    user_id = callback.from_user.id
    if await is_subscribed(callback.bot, user_id, CHANNEL_ID):
        await callback.answer()
        await send_key(callback.message, user_id, access, i18n, state)
    else:
        await callback.answer(
            await i18n(user_id, "subscription-check-failed"), show_alert=True
        )


@user_keys_router.callback_query(F.data == "sel_key")
@aiogram_inject
async def sel_key(
    callback: CallbackQuery, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    user_id = callback.from_user.id
    await callback.answer(await i18n(user_id, "generation"))
    result = await access.issue_sel(user_id)
    if not result:
        await callback.message.answer(await i18n(user_id, "channel-unavailable"))
        return
    link = result.get("link") or (result.get("links") or [""])[0]
    await message_ok(callback, i18n, user_id, "sel-title", link)


@user_keys_router.callback_query(F.data == "boot")
@aiogram_inject
async def boot(
    callback: CallbackQuery,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
    state: FSMContext,
) -> None:
    """«Запустить бота»: сброс сценария + честная самопроверка панели."""
    await callback.answer()
    user_id = callback.from_user.id
    await state.clear()
    await render(
        callback,
        await i18n(user_id, "boot-check"),
        await main_menu_kb(i18n, user_id, DONATE_URL),
    )
    ok, reason = await _panel_alive(access)
    if ok:
        await callback.message.edit_text(
            await i18n(user_id, "main-menu"),
            reply_markup=await main_menu_kb(i18n, user_id, DONATE_URL),
            disable_web_page_preview=True,
        )
        return

    logger.error(f"boot/selfcheck: панель недоступна: {reason}")
    alert = await _restart_if_allowed(callback.bot, user_id, reason)
    await callback.message.edit_text(
        await i18n(user_id, alert, reason=reason[:120]),
        reply_markup=await main_menu_kb(i18n, user_id, DONATE_URL),
        disable_web_page_preview=True,
    )


async def send_channel(
    callback: CallbackQuery,
    i18n: I18n,
    user_id: int,
    *,
    title_key: str,
    value: str,
    app_url: str,
    app_btn_key: str,
) -> None:
    """Показать канал: ключ и приложение отдельными копируемыми блоками."""
    hint = await i18n(user_id, "channel-key-hint")
    text = await i18n(user_id, title_key) + f"\n\n{hint}\n<code>{value}</code>"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "copy-channel"),
            callback_data="copy-ch",
            copy_text=CopyTextButton(text=value),
        )
    )
    if app_url:
        text += (
            "\n\n"
            + await i18n(user_id, "channel-app-hint")
            + f"\n<code>{app_url}</code>"
        )
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, app_btn_key), url=app_url)
        )
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "back"), callback_data="main_menu"
        )
    )
    await render(callback, text, builder.as_markup())


@user_keys_router.callback_query(F.data == "copy-ch")
@aiogram_inject
async def copy_channel_toast(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    await callback.answer(await i18n(callback.from_user.id, "copied"))


@user_keys_router.callback_query(F.data == "tt_key")
@aiogram_inject
async def tt_key(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    user_id = callback.from_user.id
    await callback.answer()
    if not TT_SERVICE_LINK:
        logger.warning("TT: TT_SERVICE_LINK не задан в .env — канал скрыт")
        await callback.message.answer(await i18n(user_id, "channel-unavailable"))
        return
    await send_channel(
        callback,
        i18n,
        user_id,
        title_key="tt-title",
        value=TT_SERVICE_LINK,
        app_url=TT_APP_URL,
        app_btn_key="app-tt",
    )


@user_keys_router.callback_query(F.data == "awg_key")
@aiogram_inject
async def awg_key(callback: CallbackQuery, i18n: FromDishka[I18n]) -> None:
    user_id = callback.from_user.id
    await callback.answer()
    if not AWG_SERVICE_LINK:
        logger.warning("AWG: AWG_SERVICE_LINK не задан в .env — канал скрыт")
        await callback.message.answer(await i18n(user_id, "channel-unavailable"))
        return
    await send_channel(
        callback,
        i18n,
        user_id,
        title_key="awg-title",
        value=AWG_SERVICE_LINK,
        app_url=AWG_APP_URL,
        app_btn_key="app-awg",
    )


async def message_ok(
    callback: CallbackQuery, i18n: I18n, user_id: int, title_key: str, link: str
) -> None:
    await render(
        callback,
        await i18n(user_id, title_key) + f"\n\n<code>{link}</code>",
        await keys_kb(i18n, user_id),
    )


# ---------------------------------------------------------------- самопроверка
async def _panel_alive(access: AccessService) -> tuple[bool, str]:
    """Пинг панели: GET /panel/api/server/status с коротким таймаутом."""
    try:
        await access.vpn.panel._request("GET", "/panel/api/server/status")
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


_BG_TASKS: set = set()


async def _restart_if_allowed(bot, user_id: int, reason: str) -> str:
    """Перезапуск сервиса не чаще раза в 10 минут + уведомление админу."""
    import asyncio
    import os
    import subprocess
    import time as _time

    admin_id = 0
    raw = os.getenv("ADMIN_ID") or os.getenv("TG__ADMIN_IDS", "")
    for chunk in raw.replace("[", " ").replace("]", " ").replace(",", " ").split():
        if chunk.isdigit():
            admin_id = int(chunk)
            break

    guard = "/opt/vpn-bot-v2/.last_restart"
    last = 0.0
    try:
        last = float(open(guard).read().strip())
    except Exception:
        pass
    now = _time.time()

    if admin_id:
        try:
            await bot.send_message(
                admin_id,
                f"⚠️ Самопроверка: панель недоступна ({reason[:200]}). user_id={user_id}",
            )
        except Exception:
            pass

    if now - last < 600:
        return "boot-restart-blocked"

    try:
        open(guard, "w").write(str(now))
    except Exception:
        pass

    async def _do_restart() -> None:
        await asyncio.sleep(3)
        subprocess.run(["systemctl", "restart", "vpn-bot"], check=False)

    _bg = asyncio.create_task(
        _do_restart()
    )  # держим ссылку, иначе GC может убить задачу
    _BG_TASKS.add(_bg)
    _bg.add_done_callback(_BG_TASKS.discard)
    return "boot-restart"
