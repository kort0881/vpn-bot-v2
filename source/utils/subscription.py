from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger


async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Проверка подписки на канал.

    Пустой channel_id считается «проверка отключена» — не блокируем людей.
    """
    if not channel_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        status = getattr(member, "status", "")
        status = getattr(status, "value", status)
        return status in {"creator", "administrator", "member"}
    except TelegramBadRequest as exc:
        text = str(exc).lower()
        if "user not found" in text or "participant" in text:
            return False
        logger.warning(f"is_subscribed: {channel_id} -> {exc}")
        return True
    except TelegramForbiddenError as exc:
        logger.warning(f"is_subscribed: бот не в канале {channel_id}: {exc}")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"is_subscribed: ошибка проверки {channel_id}: {exc}")
        return True
