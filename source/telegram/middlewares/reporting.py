import traceback

from aiogram import BaseMiddleware
from aiogram import Bot
from aiogram.types import ErrorEvent
from collections.abc import Awaitable
from collections.abc import Callable
from loguru import logger
from typing import Any


class ErrorReportingMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: list[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[ErrorEvent, dict[str, Any]], Awaitable[Any]],
        event: ErrorEvent,
        data: dict[str, Any],
    ) -> Any:
        try:
            error_message = f"An error occurred:: {event.exception}"

            traceback_info = traceback.format_exc()
            shortened_traceback = "\n".join(traceback_info.splitlines()[-5:])

            details = f"Details:\n\n{shortened_traceback}"
            full_message = f"{error_message}\n\n{details}"

            # 01-11-26: ошибки хендлеров владельцу в TG не шлём — только ops-лог
            try:
                import time as _t
                with open("/var/log/ops_alerts.log", "a") as _f:
                    _f.write("%s [bot_error] %s\n" % (
                        _t.strftime("%Y-%m-%d %H:%M:%S"),
                        full_message.replace("\n", " | ")[:1500]))
            except Exception:
                pass

        except Exception as e:
            logger.error(e)

        return await handler(event, data)
