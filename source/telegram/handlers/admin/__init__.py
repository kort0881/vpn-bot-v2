from aiogram import Router

from .selfcheck import selfcheck_router
from .vpn import admin_vpn_router


def setup_admin_routers() -> Router:
    router = Router(name=__name__)
    router.include_routers(admin_vpn_router, selfcheck_router)
    return router
