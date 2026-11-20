# Stack scaffold — local run

EarthPulse GeoAICubes Step 0 skeleton: library + CLI, FastAPI, Svelte viewer, Docker Compose (API, UI, MinIO).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — `uv sync` (includes dev tools when you run checks)
- Viewer: [Bun](https://bun.sh/) — `cd apps/viewer && bun install`
- Compose: Docker with `docker compose`

## Quality checks

```bash
uv sync
make check    # ruff check, ruff format --check, pytest (integration + unit)
```

GitHub Actions runs the same on push/PR to `main`: [`.github/workflows/check.yml`](../.github/workflows/check.yml).

## Native dev (no Docker)

| Service | Command | URL |
|---------|---------|-----|
| API | `make api` | http://localhost:8000/health |
| API OpenAPI | (with API running) | http://localhost:8000/docs |
| Viewer | `make ui` | http://localhost:5173 |
| MinIO (optional) | `make minio-up` | S3 :9000, console :9001 |

Set `GEOAICUBES_API_PORT` and `VITE_API_BASE_URL` via `config/.env.example` (copy to `.env` locally; never commit secrets).

## Docker Compose

```bash
make up       # foreground, rebuild
make up-d     # detached — viewer http://localhost:5173
make logs     # follow api + ui
make down     # stop stack
```

Compose file: `deploy/docker-compose.yml` · env template: `config/.env.example`.

## CLI smoke

```bash
uv run geoaicubes ok
```

## Workflow UI test

Keep the stack running, then run Cursor `/test` (see `tests/e2e/README.md`).