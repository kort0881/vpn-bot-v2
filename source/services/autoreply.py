"""Автоответчик на типовые вопросы: без LLM, локальный матчинг строк.

Перенесено из autoreply.py (старый бот). Тексты ответов живут в
locales/ru/messages.ftl под ключами autoreply-*, здесь только правила.
"""

from __future__ import annotations

import re
import time

# Латиница -> кириллица: юзер пишет на EN-раскладке («vpn» = «впн»).
_LAYOUT = str.maketrans(
    {
        "q": "й", "w": "ц", "e": "у", "r": "к", "t": "е", "y": "н", "u": "г",
        "i": "ш", "o": "щ", "p": "з", "[": "х", "]": "ъ",
        "a": "ф", "s": "ы", "d": "в", "f": "а", "g": "п", "h": "р", "j": "о",
        "k": "л", "l": "д", ";": "ж", "'": "э",
        "z": "я", "x": "ч", "c": "с", "v": "м", "b": "и", "n": "т", "m": "ь",
        ",": "б", ".": "ю",
    }
)


def expand(text: str) -> str:
    low = (text or "").lower().strip()
    return low + " ||| " + low.translate(_LAYOUT)


# (имя правила = суффикс ключа autoreply-<name>, подстроки). Первое совпадение побеждает.
RULES: list[tuple[str, list[str]]] = [
    (
        "torrent",
        ["торрент", "torrent", "торент", "торрен", "раздач", "qbit", "трансмишн", "transmission"],
    ),
    (
        "key-lost",
        [
            "потерял доступ", "нет доступ", "пропал доступ", "удалил доступ", "мой доступ",
            "обновить доступ", "сгенерир", "где доступ", "где ссылк", "где мой доступ",
            "как получить доступ", "как получить ссылк", "нет ссылк", "а где ссылк",
            "как найти ссылк", "куда делся доступ", "почему нет доступ",
        ],
    ),
    ("free", ["бесплат", "фри", "free", "даром", "халяв", "bесплат"]),
    (
        "not-working",
        [
            "не работает", "не подключа", "не коннект", "ошибк", "error", "не грузит",
            "не открывает", "сломал", "перестал работ", "нет связи", "не соединя",
        ],
    ),
    (
        "howto",
        [
            "как подключ", "как настро", "как пользов", "не знаю как", "инструкц", "куда встав",
            "как установ", "help", "помогите настро", "что делать", "впн", "vpn",
            "дай доступ", "хочу доступ", "нужен доступ", "дай впн", "хочу впн", "нужен впн",
        ],
    ),
    (
        "slow",
        ["тормоз", "медленн", "скорост", "лагает", "плохо работ", "хреново работ", "тормозит", "высокий пинг"],
    ),
    (
        "pay",
        [
            "оплат", "вариант", "купить", "плат", "цена", "стоимость", "чаевые", "donate",
            "сколько сто", "сколько это сто", "почём", "почем", "за сколько", "сколько денег",
        ],
    ),
]

_LINK_RE = re.compile(
    r"(vless://|vmess://|ss://|trojan://|https?://|/sub/|\bsub/\d)", re.IGNORECASE
)

COOLDOWN = 6 * 3600
LINK_COOLDOWN = 15 * 60
_last_hit: dict[tuple[int, str], float] = {}


def looks_like_link(text: str) -> bool:
    return bool(text) and bool(_LINK_RE.search(text))


def match(user_id: int, text: str) -> str | None:
    """Вернуть имя правила (или 'link'), если есть автоответ и не истёк кулдаун."""
    if not text:
        return None
    now = time.time()

    if looks_like_link(text):
        if now - _last_hit.get((user_id, "link"), 0) >= LINK_COOLDOWN:
            _last_hit[(user_id, "link")] = now
            return "link"
        return None

    hay = expand(text)
    for name, needles in RULES:
        for needle in needles:
            if needle in hay:
                key = (user_id, name)
                if now - _last_hit.get(key, 0) < COOLDOWN:
                    return None
                _last_hit[key] = now
                return name
    return None
