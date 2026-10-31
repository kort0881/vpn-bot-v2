"""Клавиатуры VPN-бота.

Все подписи берутся из locales/ru/buttons.ftl через I18n, поэтому в хендлерах
нет ни одного текста кнопки.
"""

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from source.utils import I18n


async def _btn(i18n: I18n, user_id: int, key: str, **kwargs) -> str:
    return await i18n(user_id, f"btn-{key}", **kwargs)


async def main_menu_kb(i18n: I18n, user_id: int, donate_url: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key")
    )
    if donate_url:
        builder.row(InlineKeyboardButton(text=await i18n(user_id, "support-project"), url=donate_url))
    else:
        builder.row(InlineKeyboardButton(text=await i18n(user_id, "support-project"), callback_data="donate"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "sel-key"), callback_data="sel_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "tt-key"), callback_data="tt_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "awg-key"), callback_data="awg_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "xhttp-key"), callback_data="xhttp_key"))
    return builder.as_markup()


async def my_key_empty_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "get-key"), callback_data="get_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def keys_kb(i18n: I18n, user_id: int, has_xhttp: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "refresh-key"), callback_data="refresh_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "copy-link"), callback_data="copy_sub"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "help"), callback_data="help"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "donate"), callback_data="donate"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "tt-key"), callback_data="tt_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "awg-key"), callback_data="awg_key"))
    if has_xhttp:
        builder.row(
            InlineKeyboardButton(text=await i18n(user_id, "xhttp-key"), callback_data="xhttp_key")
        )
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def copy_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "instruction"), callback_data="help"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "copy-happ"), callback_data="copy_happ"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def help_kb(i18n: I18n, user_id: int, invite_url: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if invite_url:
        builder.row(InlineKeyboardButton(text=await i18n(user_id, "my-key"), url=invite_url))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "trouble"), callback_data="trouble_help"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def trouble_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "my-key"), callback_data="my_key"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "back"), callback_data="help"))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def donate_kb(i18n: I18n, user_id: int, donate_url: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if donate_url:
        builder.row(InlineKeyboardButton(text=await i18n(user_id, "donate"), url=donate_url))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()


async def subscription_kb(i18n: I18n, user_id: int, channel_url: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if channel_url:
        url = channel_url if channel_url.startswith("http") else f"https://t.me/{channel_url.lstrip('@')}"
        builder.row(InlineKeyboardButton(text=await i18n(user_id, "subscribe"), url=url))
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "check-sub"), callback_data="check_sub"))
    return builder.as_markup()


async def back_to_menu_kb(i18n: I18n, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=await i18n(user_id, "main-menu"), callback_data="main_menu"))
    return builder.as_markup()
