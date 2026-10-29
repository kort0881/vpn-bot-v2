from aiogram import Router

from .commands import user_commands_router
from .keys import user_keys_router
from .pages import user_pages_router
from .support import user_support_router
from .survey import user_survey_router


def setup_user_routers() -> Router:
    router = Router(name=__name__)
    router.include_routers(
        user_commands_router,
        user_pages_router,
        user_keys_router,
        user_survey_router,
        user_support_router,
    )
    return router
