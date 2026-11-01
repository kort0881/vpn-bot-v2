"""Навигация «книга»: каждая страница знает своего родителя.

Правило: «◀️ Назад» ведёт ровно на один шаг вверх, а не в главное меню.
Родителя задаём один раз здесь — новые экраны добавляются без копипасты.
"""

from __future__ import annotations

from aiogram.types import CallbackQuery

# страница -> её родитель ("" = корень, главное меню)
PARENTS: dict[str, str] = {
    "main_menu": "",
    "my_key": "main_menu",
    "get_key": "main_menu",
    "help": "main_menu",
    "trouble_help": "help",
    "donate": "main_menu",
    "sel_key": "main_menu",
    "tt_key": "main_menu",
    "awg_key": "main_menu",
    "xhttp_key": "main_menu",
    "copy_sub": "my_key",
    "copy_happ": "my_key",
    "boot": "main_menu",
}


def parent_of(page: str) -> str:
    return PARENTS.get(page, "main_menu")


async def render(callback: CallbackQuery, text: str, kb) -> None:
    """Открыть страницу, отредактировав текущее сообщение (без спама в чат)."""
    try:
        await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    except Exception:  # noqa: BLE001 — старое сообщение/с картинкой/не изменилось
        await callback.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
