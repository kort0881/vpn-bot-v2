# Handlers

## Command handlers
Simple commands live in `user_commands_router`.
`source/telegram/handlers/user/commands.py`:
```python
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog import StartMode

from source.telegram.states import DialogSG

@user_commands_router.message(Command("dialog"))
async def dialog_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(DialogSG.first, mode=StartMode.RESET_STACK)
```

## Callback handlers
Callbacks filter by data and can use DI.
`source/telegram/handlers/user/callbacks.py`:
```python
from aiogram import F
from aiogram.types import CallbackQuery
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.services import UserService
from source.utils import I18n

@user_callbacks_router.callback_query(F.data == "language_ru")
@aiogram_inject
async def language_ru(
    callback: CallbackQuery,
    i18n: FromDishka[I18n],
    user_service: FromDishka[UserService],
) -> None:
    await callback.answer("")
    await user_service.update_user(callback.from_user.id, {"language_code": "ru"})
    i18n.invalidate_cache(callback.from_user.id)
```

## FSM handlers
Use states to drive multi-step flows.
`source/telegram/handlers/user/fsm.py`:
```python
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.telegram.filters import AgeValidator
from source.telegram.states import FormSG
from source.utils import I18n

@user_fsm_router.message(FormSG.name)
@aiogram_inject
async def process_name(
    message: Message, state: FSMContext, i18n: FromDishka[I18n]
) -> None:
    await state.update_data(name=message.text)
    await state.set_state(FormSG.age)
    await message.answer(await i18n(message.from_user.id, "fsm-enter-age"))

@user_fsm_router.message(FormSG.age, AgeValidator())
@aiogram_inject
async def process_age(
    message: Message, state: FSMContext, i18n: FromDishka[I18n]
) -> None:
    data = await state.get_data()
    await message.answer(
        await i18n(
            message.from_user.id,
            "fsm-result",
            name=data["name"],
            age=message.text,
        )
    )
    await state.clear()
```

## With Dependency Injection (Dishka)
Inject services or utilities with `FromDishka` and `@aiogram_inject`.
`source/telegram/handlers/user/commands.py`:
```python
from aiogram.filters import CommandStart
from aiogram.types import Message
from dishka import FromDishka
from dishka.integrations.aiogram import inject as aiogram_inject

from source.services import UserService
from source.utils import I18n

@user_commands_router.message(CommandStart())
@aiogram_inject
async def start(
    message: Message,
    user_service: FromDishka[UserService],
    i18n: FromDishka[I18n],
) -> None:
    await user_service.register_user(message.from_user.id)
    await message.answer(await i18n(message.from_user.id, "greeting"))
```
