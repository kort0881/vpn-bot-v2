IMAGE_NAME = aiogram-bot-template
PYTHON_MAIN = source/__main__.py
PROJECT_DIR = source/
VENV_DIR = .venv

.PHONY: install run lint clean docker-build docker-up docker-down docker-logs help all venv dev-up dev-down dev-logs seed health migration

default: help

help:
	@echo "Available make commands:"
	@echo "  venv          - Create a virtual environment (using uv and pyproject.toml)"
	@echo "  install       - Install project dependencies (using uv and pyproject.toml)"
	@echo "  run           - Run the bot locally (in the created environment)"
	@echo "  lint          - Check the code and format (in the created environment)"
	@echo "  clean         - Delete temporary files and caches"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-up     - Launch the project via docker compose"
	@echo "  docker-down   - Stop the project via docker compose"
	@echo "  docker-logs   - View Docker container logs (optional: SERVICE=service_name)" 
	@echo "  all           - Launch lint"

venv: $(VENV_DIR)
$(VENV_DIR):
	@echo "Creating a virtual environment in $(VENV_DIR)..."
	uv venv
	@echo "The virtual environment has been created."

install: venv
	@echo "Installing dependencies..."
	uv pip install -e .[dev]
	@echo "Dependencies installed."

run:
	@echo "Launch project..."
	uv run python $(PYTHON_MAIN)

lint:
	@echo "Starting checks..."
	uv run python -m ruff check $(PROJECT_DIR) --config pyproject.toml --fix
	uv run python -m isort $(PROJECT_DIR)
	uv run python -m mypy $(PROJECT_DIR) --config-file pyproject.toml
	uv run python -m black $(PROJECT_DIR) --config pyproject.toml
	@echo "Checks completed!"

clean:
	@echo "Start cleaning..."
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	rm -rf .mypy_cache .ruff_cache .egg-info
	@echo "Cleaning done!"

docker-build:
	@echo "Launch creating docker image..."
	docker compose down
	docker build -t $(IMAGE_NAME) .

docker-up:
	@echo "Starting container..."
	docker compose up -d

docker-down:
	@echo "Starting container deletion..."
	docker compose down
	@echo "Container removed!"

docker-logs:
	@echo "Просмотр логов для сервиса: $(SERVICE)..."
	docker compose logs -f -t $(SERVICE)

dev-up:
	@echo "Starting development services (DB, Redis)..."
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	@echo "Stopping development services..."
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

seed:
	@echo "Seeding database with test data..."
	uv run python scripts/db_seed.py

health:
	@echo "Checking services health..."
	uv run python scripts/health_check.py

migration:
	@echo "Creating new migration: $(MESSAGE)"
	chmod +x scripts/create_migration.sh
	./scripts/create_migration.sh "$(MESSAGE)"

all: lint
