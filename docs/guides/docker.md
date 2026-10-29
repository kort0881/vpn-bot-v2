# Docker

## Development commands
Use the dev compose file for local DB/Redis.
```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml logs -f
docker compose -f docker-compose.dev.yml down
```

## Production commands
Use Makefile wrappers for the main compose file.
```bash
make docker-build
make docker-up
make docker-logs SERVICE=bot
```

## Useful commands
Quick helpers for common docker checks.
```bash
docker compose ps
docker compose logs -f --tail=200
docker compose exec db psql -U $DB__USER -d $DB__NAME
```
