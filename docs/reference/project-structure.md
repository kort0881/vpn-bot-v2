# Project Structure

## Tree
```text
aiogram-bot-template/
├── docs/
├── migrations/
├── scripts/
├── source/
│   ├── config/
│   ├── database/
│   ├── factory/
│   ├── infrastructure/
│   ├── locales/
│   ├── services/
│   ├── telegram/
│   └── utils/
├── tests/
├── alembic.ini
├── docker-compose.dev.yml
├── docker-compose.yml
├── pyproject.toml
└── source/__main__.py
```

## Folders
- `docs/` short guides and reference docs.
- `source/config/` pydantic settings and env loading.
- `source/database/` models, repositories, UnitOfWork.
- `source/services/` business logic layer.
- `source/telegram/` handlers, routers, filters, dialogs.
- `source/factory/` bot/dispatcher/app/container wiring.
- `source/infrastructure/` cache and external integrations.
- `source/utils/` logger, i18n, helpers.
- `migrations/` Alembic migration scripts.
- `scripts/` CLI helpers for ops tasks.

## Key files
- `.env.example` sample configuration values.
- `alembic.ini` Alembic config.
- `docker-compose.yml` production compose stack.
- `docker-compose.dev.yml` local DB/Redis stack.
- `source/__main__.py` app entry point.
