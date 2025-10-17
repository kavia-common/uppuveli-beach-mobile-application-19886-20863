# Developer convenience targets for BackendAPI

.PHONY: help install run dev openapi migrate-up migrate-down migrate-rev seed lint fmt diag create-admin

help:
	@echo "BackendAPI Makefile targets:"
	@echo "  install        Install Python dependencies"
	@echo "  run            Run the API with uvicorn"
	@echo "  dev            Run API in reload mode"
	@echo "  openapi        Generate OpenAPI JSON to interfaces/openapi.json"
	@echo "  migrate-up     Apply alembic migrations to head"
	@echo "  migrate-down   Downgrade alembic by one revision"
	@echo "  migrate-rev    Create new alembic revision with message: make migrate-rev m='message'"
	@echo "  seed           Seed the database with initial data"
	@echo "  create-admin   Create or update an admin user: make create-admin EMAIL=... PASSWORD=... [NAME=...] [SUPERUSER=1] [PRINT_TOKEN=1]"
	@echo "  lint           Run flake8"
	@echo "  fmt            Run auto-format with black (if installed)"

install:
	pip install -r requirements.txt

run:
	uvicorn src.api.main:app

dev:
	uvicorn src.api.main:app --reload

openapi:
	python -m src.api.generate_openapi

migrate-up:
	alembic -c alembic.ini upgrade head

migrate-up-py:
	python -m src.db.run_migrations upgrade head

migrate-down:
	alembic -c alembic.ini downgrade -1

migrate-rev:
	@if [ -z "$(m)" ]; then echo "Please provide a message: make migrate-rev m='message'"; exit 1; fi
	alembic -c alembic.ini revision -m "$(m)" --autogenerate

seed:
	python -m src.db.seed

lint:
	flake8 src

fmt:
	@if command -v black >/dev/null 2>&1; then black src; else echo "black not installed; skipping"; fi

diag:
	python -m src.db.diagnostics

# Create or update an admin user (idempotent)
# Usage:
#   make create-admin EMAIL=admin@example.com PASSWORD='StrongPass123!' [NAME='Admin'] [SUPERUSER=1] [PRINT_TOKEN=1]
create-admin:
	@if [ -z "$(EMAIL)" ] || [ -z "$(PASSWORD)" ]; then echo "Usage: make create-admin EMAIL=... PASSWORD=... [NAME=...] [SUPERUSER=1] [PRINT_TOKEN=1]"; exit 1; fi; \
	PARGS="--email $(EMAIL) --password '$(PASSWORD)'"; \
	if [ -n "$(NAME)" ]; then PARGS="$$PARGS --name '$(NAME)'"; fi; \
	if [ "$(SUPERUSER)" = "1" ]; then PARGS="$$PARGS --superuser"; fi; \
	if [ "$(PRINT_TOKEN)" = "1" ]; then PARGS="$$PARGS --print-token"; fi; \
	python -m src.scripts.create_admin $$PARGS
