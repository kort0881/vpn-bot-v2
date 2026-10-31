from aiogram import Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.config.panel import CHANNEL_ID
from source.config.panel import DONATE_URL
from source.config.panel import VIP_INVITE_URL
from source.services import AccessService
from source.telegram.keyboards.vpn import donate_kb
from source.telegram.keyboards.vpn import help_kb
from source.telegram.keyboards.vpn import main_menu_kb
from source.telegram.keyboards.vpn import subscription_kb
from source.utils import I18n
from source.utils.subscription import is_subscribed

user_commands_router = Router(name=__name__)


async def banned_text(access: AccessService, i18n: I18n, user_id: int, profile) -> str:
    text = await i18n(user_id, "banned-title")
    if profile and profile.ban_reason:
        text += "\n\n" + await i18n(user_id, "banned-reason", reason=profile.ban_reason)
    show_term, days = access.ban_until_text(profile)
    if show_term:
        text += "\n\n" + await i18n(user_id, "banned-term-days", days=days)
    else:
        text += "\n\n" + await i18n(user_id, "banned-term-soon")
    return text


@user_commands_router.message(CommandStart())
@aiogram_inject
async def start(
    message: Message,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    user = message.from_user
    profile = await access.ensure_user(user.id, user.username or "")

    if profile.banned:
        await message.answer(await banned_text(access, i18n, user.id, profile))
        return

    if not await is_subscribed(message.bot, user.id, CHANNEL_ID):
        await message.answer(
            await i18n(user.id, "subscription-required"),
            reply_markup=await subscription_kb(i18n, user.id, CHANNEL_ID),
        )
        return

    keys_count = await access.keys_issued()
    text = await i18n(user.id, "start", name=user.first_name or "", keys=keys_count)
    await message.answer(text, reply_markup=await main_menu_kb(i18n, user.id, DONATE_URL))


@user_commands_router.message(Command("menu"))
@aiogram_inject
async def menu(message: Message, i18n: FromDishka[I18n]) -> None:
    await message.answer(
        await i18n(message.from_user.id, "main-menu"),
        reply_markup=await main_menu_kb(i18n, message.from_user.id, DONATE_URL),
    )


@user_commands_router.message(Command("vpn"))
@aiogram_inject
async def vpn(
    message: Message,
    state: FSMContext,
    access: FromDishka[AccessService],
    i18n: FromDishka[I18n],
) -> None:
    from source.telegram.handlers.user.keys import send_key

    await send_key(message, message.from_user.id, access, i18n, state)


@user_commands_router.message(Command("help"))
@aiogram_inject
async def help_command(message: Message, i18n: FromDishka[I18n]) -> None:
    user_id = message.from_user.id
    text = await i18n(user_id, "help-title")
    if VIP_INVITE_URL:
        text += "\n" + await i18n(user_id, "help-channel", link=VIP_INVITE_URL)
    text += "\n\n" + await i18n(user_id, "help-short")
    text += "\n\n" + await i18n(user_id, "help-warning")
    await message.answer(text, reply_markup=await help_kb(i18n, user_id, VIP_INVITE_URL))


@user_commands_router.message(Command("donate"))
@aiogram_inject
async def donate(message: Message, i18n: FromDishka[I18n]) -> None:
    user_id = message.from_user.id
    await message.answer(
        await i18n(user_id, "donate-title"), reply_markup=await donate_kb(i18n, user_id, DONATE_URL)
    )
