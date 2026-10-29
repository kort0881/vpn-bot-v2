# Getting Started

## Install
Clone, copy env, and sync deps with uv.
```bash
git clone https://github.com/your-org/aiogram-bot-template.git
cd aiogram-bot-template
cp .env.example .env
uv sync
```
Edit `.env` with your `TG__BOT_TOKEN` and admin IDs.

## Run
Polling is default; webhook mode is controlled by `TG__WEBHOOK_USE`.
```bash
uv run python source/__main__.py
```

## First Handler
Add a command to the existing user router and it is auto-registered.
`source/telegram/handlers/user/commands.py`:
```python
from aiogram.filters import Command
from aiogram.types import Message

@user_commands_router.message(Command("ping"))
async def ping(message: Message) -> None:
    await message.answer("pong")
```
`source/telegram/handlers/user/__init__.py`:
```python
router.include_router(user_commands_router)
```
