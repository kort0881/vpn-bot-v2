import asyncio
import os
import uvicorn

from dishka.integrations.aiogram import setup_dishka as setup_aiogram_dishka
from dishka.integrations.fastapi import setup_dishka as setup_fastapi_dishka
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from source.config import settings
from source.database import create_tables
from source.factory import create_app
from source.factory import create_bot
from source.factory import create_container
from source.factory import create_dispatcher
from source.utils import set_default_commands
from source.tasks.renewal import renewal_loop
from source.utils import setup_logger


async def start_polling():
    logger.info("Starting polling...")

    container = create_container()
    if settings.environment != "production":
        engine = await container.get(AsyncEngine)
        await create_tables(engine)
    bot = create_bot()
    dp = create_dispatcher()

    await set_default_commands(bot)

    setup_aiogram_dishka(container=container, router=dp, auto_inject=True)

    dp.shutdown.register(container.close)

    from source.config.panel import RENEWAL_ENABLED as renewal_enabled
    renewal_task = None
    if renewal_enabled:
        renewal_task = asyncio.create_task(renewal_loop(bot, container))
        logger.info("фоновая задача продления подписок запущена")
    else:
        logger.warning("цикл продления ВЫКЛЮЧЕН (RENEWAL_ENABLED=0) — включать только после переключения")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if renewal_task:
            renewal_task.cancel()
        await bot.session.close()


def main_webhook():
    logger.info("Starting webhook...")
    container = create_container()
    bot = create_bot()
    dp = create_dispatcher()
    app = create_app(bot=bot, dp=dp, container=container)

    setup_aiogram_dishka(container=container, router=dp)
    setup_fastapi_dishka(container=container, app=app)

    uvicorn.run(
        app,
        host=settings.webhook.host,
        port=settings.webhook.port,
        log_config=None,
    )


if __name__ == "__main__":
    setup_logger()

    if settings.tg.webhook_use:
        main_webhook()
    else:
        asyncio.run(start_polling())
