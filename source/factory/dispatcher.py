from aiogram import Dispatcher
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage

from source.config import settings
from source.telegram import setup_middlewares
from source.telegram import setup_routers


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage(
        redis=settings.redis.redis_connection(),
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )
    dp = Dispatcher(storage=storage)

    setup_middlewares(dp)
    setup_routers(dp)
    return dp
