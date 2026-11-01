"""Клавиатуры VPN-бота.

Все подписи берутся из locales/ru/buttons.ftl через I18n, поэтому в хендлерах
нет ни одного текста кнопки.
"""

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from source.config.panel import AWG_SERVICE_LINK
from source.config.panel import SEL_ENABLED
from source.config.panel import TT_SERVICE_LINK
from source.config.panel import XHTTP_ENABLED
from source.utils import I18n


async def _btn(i18n: I18n, user_id: int, key: str, **kwargs) -> str:
    return await i18n(user_id, f"btn-{key}", **kwargs)


async def _nav(
    builder: InlineKeyboardBuilder, i18n: I18n, user_id: int, back_to: str
) -> None:
    """Строка навигации: «Назад» ровно на один шаг, «В меню» — только из вложенных."""
    if not back_to:
        return
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "back"), callback_data=back_to)
    )
    if back_to != "main_menu":
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "main-menu"), callback_data="main_menu"
            )
        )


async def main_menu_kb(
    i18n: I18n, user_id: int, donate_url: str = ""
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key")
    )
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "boot"), callback_data="boot")
    )
    if SEL_ENABLED:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "sel-key"), callback_data="sel_key"
            )
        )
    if TT_SERVICE_LINK:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "tt-key"), callback_data="tt_key"
            )
        )
    if AWG_SERVICE_LINK:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "awg-key"), callback_data="awg_key"
            )
        )
    if XHTTP_ENABLED:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "xhttp-key"), callback_data="xhttp_key"
            )
        )
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "donate"), callback_data="donate")
    )
    return builder.as_markup()


async def my_key_empty_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "get-key"), callback_data="get_key"
        )
    )
    await _nav(builder, i18n, user_id, "main_menu")
    return builder.as_markup()


async def keys_kb(
    i18n: I18n, user_id: int, has_xhttp: bool = True, back_to: str = "main_menu"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "refresh-key"), callback_data="refresh_key"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "copy-link"), callback_data="copy_sub"
        )
    )
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "help"), callback_data="help")
    )
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "donate"), callback_data="donate")
    )
    if TT_SERVICE_LINK:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "tt-key"), callback_data="tt_key"
            )
        )
    if AWG_SERVICE_LINK:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "awg-key"), callback_data="awg_key"
            )
        )
    if has_xhttp and XHTTP_ENABLED:
        builder.row(
            InlineKeyboardButton(
                text=await i18n(user_id, "xhttp-key"), callback_data="xhttp_key"
            )
        )
    await _nav(builder, i18n, user_id, back_to)
    return builder.as_markup()


async def copy_kb(
    i18n: I18n, user_id: int, back_to: str = "my_key"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "instruction"), callback_data="help"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "copy-happ"), callback_data="copy_happ"
        )
    )
    await _nav(builder, i18n, user_id, back_to)
    return builder.as_markup()


async def help_kb(
    i18n: I18n,
    user_id: int,
    invite_url: str = "",
    back_to: str = "main_menu",
    post_url: str = "",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if post_url:
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, "vip-post"), url=post_url)
        )
    if invite_url:
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, "my-key"), url=invite_url)
        )
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "trouble"), callback_data="trouble_help"
        )
    )
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key")
    )
    await _nav(builder, i18n, user_id, back_to)
    return builder.as_markup()


async def trouble_kb(
    i18n: I18n, user_id: int, back_to: str = "help"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key")
    )
    await _nav(builder, i18n, user_id, back_to)
    return builder.as_markup()


async def donate_kb(
    i18n: I18n, user_id: int, donate_url: str = "", back_to: str = "main_menu"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if donate_url:
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, "donate"), url=donate_url)
        )
    await _nav(builder, i18n, user_id, back_to)
    return builder.as_markup()


async def subscription_kb(
    i18n: I18n, user_id: int, channel_url: str = ""
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if channel_url:
        url = (
            channel_url
            if channel_url.startswith("http")
            else f"https://t.me/{channel_url.lstrip('@')}"
        )
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, "subscribe"), url=url)
        )
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "check-sub"), callback_data="check_sub"
        )
    )
    return builder.as_markup()


async def back_to_menu_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=await i18n(user_id, "main-menu"), callback_data="main_menu"
        )
    )
    return builder.as_markup()
