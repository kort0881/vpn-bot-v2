# Deployment

## Docker Compose
Use `docker-compose.yml` for bot + db + redis.
```bash
docker compose up -d
docker compose logs -f bot
docker compose down
```

## Systemd service
Minimal service unit for a webhook or polling run.
```ini
[Unit]
Description=Aiogram Bot
After=network.target

[Service]
WorkingDirectory=/opt/aiogram-bot-template
EnvironmentFile=/opt/aiogram-bot-template/.env
ExecStart=/usr/bin/uv run python source/__main__.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Before production checklist
- Set `ENVIRONMENT=production` in `.env`.
- Set `TG__WEBHOOK_USE=True` and `WEBHOOK__*` for webhook mode.
- Run migrations: `uv run alembic upgrade head`.
- Verify DB/Redis connectivity and bot token.
