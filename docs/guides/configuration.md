# Configuration

## Required variables
Set these in `.env` before running; Settings loads them all.
```env
TG__BOT_TOKEN=1234567890:ABCDEF
TG__ADMIN_IDS=[5252216460]
TG__WEBHOOK_USE=False
TG__WEBHOOK_PATH=/telegram

WEBHOOK__URL=https://example.com
WEBHOOK__HOST=0.0.0.0
WEBHOOK__PORT=8443
WEBHOOK__PATH=/webhook
WEBHOOK__SECRET=long_random_secret

DB__HOST=db
DB__PORT=5432
DB__USER=default
DB__PASSWORD=password
DB__NAME=telegram_bot_template

REDIS__HOST=redis
REDIS__PORT=6379
REDIS__USER=default
REDIS__PASSWORD=password
REDIS__DB=0
```

## Optional variables
`ENVIRONMENT` defaults to `production`.
```env
ENVIRONMENT=development
```

## Examples
Development example:
```env
ENVIRONMENT=development
TG__WEBHOOK_USE=False
WEBHOOK__HOST=0.0.0.0
```
Production example:
```env
ENVIRONMENT=production
TG__WEBHOOK_USE=True
WEBHOOK__URL=https://bot.example.com
```
