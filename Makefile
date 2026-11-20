COMPOSE_FILE := deploy/docker-compose.yml
COMPOSE_ENV_FILE := config/.env.example

VIEWER_DIR := apps/viewer

.PHONY: help api ui build up up-build down

help:
	@echo "Local dev (requires: uv sync; ui also needs bun install in $(VIEWER_DIR))"
	@echo ""
	@echo "  make api               FastAPI via uvicorn (reload; port from GEOAICUBES_API_PORT)"
	@echo "  make ui                Viewer Vite dev server ($(VIEWER_DIR))"
	@echo "  make build             Rebuild api/ui images (after Dockerfile or dep changes)"
	@echo "  make up                docker compose up (reuse existing images; UI :5173)"
	@echo "  make down              docker compose down ($(COMPOSE_FILE))"

api:
	GEOAICUBES_API_RELOAD=true uv run python -m geoaicubes.api.main

ui:
	cd $(VIEWER_DIR) && bun run dev

build:
	docker compose -f $(COMPOSE_FILE) --env-file $(COMPOSE_ENV_FILE) build

up:
	docker compose -f $(COMPOSE_FILE) --env-file $(COMPOSE_ENV_FILE) up

down:
	docker compose -f $(COMPOSE_FILE) --env-file $(COMPOSE_ENV_FILE) down