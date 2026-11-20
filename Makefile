COMPOSE_FILE := deploy/docker-compose.yml
COMPOSE_ENV_FILE := config/.env.example

VIEWER_DIR := apps/viewer

COMPOSE := docker compose -f $(COMPOSE_FILE) --env-file $(COMPOSE_ENV_FILE)

RUFF_PATHS := src tests

.PHONY: help check check-docs check-notebooks test api ui build up up-d down logs minio-up minio-down inventory-export

INVENTORY_EXPORT := docs/data-plane/inventory-export.json

help:
	@echo "Local dev (requires: uv sync; ui also needs bun install in $(VIEWER_DIR))"
	@echo "pytest: make test (integration + unit) · e2e: make up → Cursor /test"
	@echo ""
	@echo "  make check             ruff (src, tests) + format + docs smoke + pytest"
	@echo "  make check-notebooks   optional ruff on notebooks/"
	@echo "  make test              pytest (tests/integration, tests/unit)"
	@echo "  make api               FastAPI via uvicorn (reload; port from GEOAICUBES_API_PORT)"
	@echo "  make ui                Viewer Vite dev server ($(VIEWER_DIR))"
	@echo "  make build             Rebuild api/ui images (after Dockerfile or dep changes)"
	@echo "  make up                docker compose up --build (foreground; streams logs here)"
	@echo "  make up-d              docker compose up -d (background; open http://localhost:5173)"
	@echo "  make logs              follow api + ui container logs (after up-d)"
	@echo "  make minio-up          MinIO only (:9000 / :9001) for native API/UI dev"
	@echo "  make minio-down        Stop MinIO container"
	@echo "  make inventory-export  Snapshot GET /api/v1/inventory/zarr → $(INVENTORY_EXPORT)"
	@echo "  make down              docker compose down ($(COMPOSE_FILE))"

check:
	uv run ruff check $(RUFF_PATHS)
	uv run ruff format --check $(RUFF_PATHS)
	$(MAKE) check-docs
	$(MAKE) test

check-docs:
	@test -s docs/demo-config.md
	@test -s docs/program/preflight-log.md

check-notebooks:
	uv run ruff check notebooks

test:
	uv run pytest

api:
	GEOAICUBES_API_RELOAD=true uv run python -m geoaicubes.api.main

ui:
	cd $(VIEWER_DIR) && bun run dev

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

up-d:
	$(COMPOSE) up -d --build
	@echo ""
	@echo "Stack running in the background (no Vite banner in this terminal)."
	@echo "  Viewer:  http://localhost:5173"
	@echo "  API:     http://localhost:8000/health"
	@echo "  MinIO:   http://localhost:9001"
	@echo "  Logs:    make logs"
	@echo "  Stop:    make down"

logs:
	$(COMPOSE) logs -f ui api

minio-up:
	$(COMPOSE) up -d minio
	@echo "MinIO S3: http://localhost:9000  console: http://localhost:9001"
	@echo "In-place data dir: repo data/ (create buckets from console or mc if you need S3 clients)"

minio-down:
	$(COMPOSE) stop minio

down:
	$(COMPOSE) down

inventory-export:
	uv run geoaicubes inventory-export --output $(INVENTORY_EXPORT)