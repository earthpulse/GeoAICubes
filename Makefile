COMPOSE_FILE := deploy/docker-compose.yml
COMPOSE_ENV_FILE := config/.env.example

VIEWER_DIR := apps/viewer

COMPOSE := docker compose -f $(COMPOSE_FILE) --env-file $(COMPOSE_ENV_FILE)

.PHONY: help api ui build up up-d down logs minio-up minio-down

help:
	@echo "Local dev (requires: uv sync; ui also needs bun install in $(VIEWER_DIR))"
	@echo "UI test: make up (keep running) → Cursor /test"
	@echo ""
	@echo "  make api               FastAPI via uvicorn (reload; port from GEOAICUBES_API_PORT)"
	@echo "  make ui                Viewer Vite dev server ($(VIEWER_DIR))"
	@echo "  make build             Rebuild api/ui images (after Dockerfile or dep changes)"
	@echo "  make up                docker compose up (foreground; streams Vite logs here)"
	@echo "  make up-d              docker compose up -d (background; open http://localhost:5173)"
	@echo "  make logs              follow api + ui container logs (after up-d)"
	@echo "  make minio-up          MinIO only in Docker (:9000 / :9001) for native API/UI dev"
	@echo "  make minio-down        Stop MinIO container"
	@echo "  make down              docker compose down ($(COMPOSE_FILE))"

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
	@echo "Native API: demo.yaml uses GEOAICUBES_STORAGE__ENDPOINT_URL=http://localhost:9000"

minio-down:
	$(COMPOSE) stop minio

down:
	$(COMPOSE) down