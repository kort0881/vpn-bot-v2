"""Опрос в канале: голоса по кнопкам sv:<номер>.

Старый survey.py писал (user, вариант) в poll_answers с poll_id
'channel_survey_2026-10-09'. Здесь то же самое, но через репозиторий.
"""

import json

from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject
from loguru import logger

from source.services import AccessService
from source.utils import I18n

user_survey_router = Router(name=__name__)

POLL_ID = "channel_survey_2026-10-09"
LABELS = {
    1: "Всё работает стабильно",
    2: "Работает, но иногда отваливается",
    3: "Медленно, но работает",
    4: "Не работает / не подключается",
}


@user_survey_router.callback_query(F.data.startswith("sv:"))
@aiogram_inject
async def survey_vote(
    callback: CallbackQuery, access: FromDishka[AccessService], i18n: FromDishka[I18n]
) -> None:
    try:
        option = int((callback.data or "").split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    user = callback.from_user
    try:
        await access.save_poll_answer(
            poll_id=POLL_ID,
            telegram_id=user.id,
            username=user.username or "",
            full_name=user.full_name or "",
            option_ids=json.dumps([option - 1]),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"survey record error: {exc}")
    await callback.answer("Спасибо! Записали: " + LABELS.get(option, "?"))
    logger.info(f"SURVEY_VOTE user={user.id} opt={option}")
