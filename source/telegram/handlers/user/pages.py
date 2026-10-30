"""Постраничный интерфейс бота: одна страница = один экран.

Навигация как в книге: «◀ Назад» / «Вперёд ▶» и «🏠 Главное меню».
Сообщение при перелистывании редактируется на месте (не заваливает чат).

Страницы:
  1. Мой доступ — статус, трафик, срок, лимит устройств
  2. Ключи — ссылка-подписка и подсказка, что с ней делать
  3. Другие каналы — Selectel, XHTTP, TrustTunnel, AmneziaWG
  4. Инструкция — короткие шаги подключения
  5. Поддержка — как написать нам
"""

from __future__ import annotations

from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.config.panel import SUB_URL
from source.services import AccessService
from source.utils import I18n

user_pages_router = Router(name=__name__)

TOTAL_PAGES = 5


def _sub_url(user_id: int) -> str:
    return SUB_URL.format(user_id=user_id)


async def build_page_text(
    page: int, user_id: int, access: AccessService, i18n: I18n
) -> str:
    """Текст одной страницы. Никакой логики, кроме выбора данных."""
    user = await access.get_user(user_id)
    has_key = access.has_active_key(user)

    if page == 1:
        parts = [await i18n(user_id, "page-1-title")]
        if has_key and user is not None:
            parts.append(await i18n(user_id, "keys-stats", **access.stats_text(user)))
        else:
            parts.append(await i18n(user_id, "page-no-access"))
        return "\n\n".join(parts)

    if page == 2:
        parts = [await i18n(user_id, "page-2-title")]
        if not has_key:
            parts.append(await i18n(user_id, "page-no-access"))
            return "\n\n".join(parts)
        parts.append(f"<code>{_sub_url(user_id)}</code>")
        parts.append(await i18n(user_id, "keys-hint"))
        parts.append(await i18n(user_id, "keys-stats", **access.stats_text(user)))
        return "\n\n".join(parts)

    if page == 3:
        return "\n\n".join(
            [
                await i18n(user_id, "page-3-title"),
                await i18n(user_id, "page-3-body"),
            ]
        )

    if page == 4:
        return "\n\n".join(
            [
                await i18n(user_id, "page-4-title"),
                await i18n(user_id, "help-short"),
                await i18n(user_id, "trouble-steps"),
            ]
        )

    return "\n\n".join(
        [
            await i18n(user_id, "page-5-title"),
            await i18n(user_id, "page-5-body"),
        ]
    )


async def build_page_kb(page: int, user_id: int, i18n: I18n):
    builder = InlineKeyboardBuilder()

    if page == 2:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "page-refresh"), callback_data="page_refresh"
            )
        )

    if page == 3:
        builder.row(
            InlineKeyboardButton(text="🔷 Selectel · 3 ТБ", callback_data="sel_key")
        )
        builder.row(
            InlineKeyboardButton(text="🧪 XHTTP · 300 ГБ", callback_data="xhttp_key")
        )
        builder.row(InlineKeyboardButton(text="🛡 TrustTunnel", callback_data="tt_key"))
        builder.row(InlineKeyboardButton(text="🛡 AmneziaWG", callback_data="awg_key"))

    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text=await i18n(user_id, "page-prev"), callback_data=f"page:{page - 1}"
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=await i18n(user_id, "page-counter", page=page, total=TOTAL_PAGES),
            callback_data="page:noop",
        )
    )
    if page < TOTAL_PAGES:
        nav.append(
            InlineKeyboardButton(
                text=await i18n(user_id, "page-next"), callback_data=f"page:{page + 1}"
            )
        )
    builder.row(*nav)

    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "main-menu"), callback_data="main_menu"
        )
    )
    return builder.as_markup()


async def open_page(
    callback: CallbackQuery, page: int, access: AccessService, i18n: I18n
) -> None:
    """Показать страницу, отредактировав текущее сообщение."""
    page = max(1, min(TOTAL_PAGES, page))
    user_id = callback.from_user.id
    text = await build_page_text(page, user_id, access, i18n)
    kb = await build_page_kb(page, user_id, i18n)
    try:
        await callback.message.edit_text(
            text, reply_markup=kb, disable_web_page_preview=True
        )
    except Exception:  # noqa: BLE001 — сообщение не редактируется (старое/с картинкой)
        await callback.message.answer(
            text, reply_markup=kb, disable_web_page_preview=True
        )


@user_pages_router.callback_query(F.data == "page:noop")
async def page_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@user_pages_router.callback_query(F.data.startswith("page:"))
@aiogram_inject
async def page_nav(
    callback: CallbackQuery,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    raw = (callback.data or "").split(":", 1)[1]
    if not raw.isdigit():
        await callback.answer()
        return
    await callback.answer()
    await open_page(callback, int(raw), access, i18n)


@user_pages_router.callback_query(F.data == "my_key")
@aiogram_inject
async def my_key_page(
    callback: CallbackQuery,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    """«Мой доступ» теперь открывает первую страницу книги."""
    await callback.answer()
    await open_page(callback, 1, access, i18n)


@user_pages_router.callback_query(F.data == "page_refresh")
@aiogram_inject
async def page_refresh(
    callback: CallbackQuery,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    """Обновить ключ, не уходя со страницы «Ключи»."""
    user_id = callback.from_user.id
    user = await access.get_user(user_id)
    if not access.has_active_key(user):
        await callback.answer(await i18n(user_id, "refresh-no-access"), show_alert=True)
        return
    await callback.answer(await i18n(user_id, "refresh-progress"))
    result = await access.refresh_key(user_id)
    if not result.get("ok"):
        await open_page(callback, 2, access, i18n)
        await callback.message.answer(
            await i18n(user_id, "refresh-fail", detail=str(result.get("reason"))[:120])
        )
        return
    await open_page(callback, 2, access, i18n)
