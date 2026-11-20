# Stack scaffold — local run

EarthPulse GeoAICubes Step 0–1 stack: library + CLI, FastAPI (inventory + mounted TiTiler), Svelte viewer, Docker Compose (API, UI, MinIO). Storage layout and env keys: [`demo-config.md`](demo-config.md).

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
| Zarr inventory (list) | (with API running) | http://localhost:8000/api/v1/inventory/zarr |
| Zarr inventory (one store) | (with API running) | http://localhost:8000/api/v1/inventory/zarr/{id} |
| Zarr tiles (TiTiler mount) | (with API running) | http://localhost:8000/tiles/zarr/… (see below) |
| Viewer | `make ui` | http://localhost:5173 |
| MinIO (optional) | `make minio-up` | S3 :9000, console :9001 |

Native API defaults to `GEOAICUBES_STORAGE__DISCOVERY_MODE=filesystem` (`config/.env.example`): inventory and tiles read Zarr from the repo `data/` tree. For S3-backed discovery against host MinIO, set `GEOAICUBES_STORAGE__DISCOVERY_MODE=s3` and align credentials with `MINIO_*`.

### Step 1 API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness (`status`, `version`) |
| `GET` | `/api/v1/inventory/zarr` | List discovered `.zarr` stores |
| `GET` | `/api/v1/inventory/zarr/{id}` | One store metadata + `tile_url_template` |
| `GET` | `/tiles/zarr/tiles/{tileMatrixSetId}/{z}/{x}/{y}.png` | PNG tile (`?url=`, `variable`, `rescale`, optional `sel`) |
| `GET` | `/tiles/zarr/{tileMatrixSetId}/tilejson.json` | TileJSON (same query string as templates) |

Inventory shapes and field meanings: [`data-plane/inventory-schema.md`](data-plane/inventory-schema.md). Tile query parameters: [`data-plane/titiler-integration.md`](data-plane/titiler-integration.md). Step 1 uses `tileMatrixSetId=WebMercatorQuad`.

Each inventory store exposes renderable variables under `tile_url_template` (relative paths on the API origin). The viewer prefixes them with `VITE_API_BASE_URL`; in Compose that is `http://localhost:8000` at image build time.

Example (API up, demo cube present):

```bash
curl -s http://localhost:8000/api/v1/inventory/zarr | jq '.count'
curl -s "http://localhost:8000/api/v1/inventory/zarr/Geodatacube_orto2024.zarr" | jq '.tile_url_template'
```

Set `GEOAICUBES_API_PORT` and `VITE_API_BASE_URL` via `config/.env.example` (copy to `.env` locally; never commit secrets).

## Docker Compose

```bash
make up       # foreground, rebuild
make up-d     # detached — viewer http://localhost:5173
make logs     # follow api + ui
make down     # stop stack
```

Compose file: `deploy/docker-compose.yml` · env template: `config/.env.example`.

**Live reload in Compose:** `../src` is mounted into the API container (`uvicorn --reload`); `apps/viewer/` is mounted into the UI container (Vite HMR). Rebuild images (`make build`) only when `Dockerfile.*`, `pyproject.toml` / `uv.lock`, or viewer `package.json` / `bun.lock` change — run `docker compose exec ui bun install` after viewer dependency changes.

| Compose service | Host ports | Role |
|-----------------|------------|------|
| `api` | 8000 | FastAPI: `/health`, `/api/v1/inventory/zarr`, `/tiles/zarr` (no separate TiTiler container) |
| `ui` | 5173 | Static viewer (`VITE_API_BASE_URL` → host `http://localhost:8000`) |
| `minio` | 9000 (S3), 9001 (console) | In-place object store over repo `data/` (`server /data`) |

MinIO uses an **in-place** bind mount of repo `data/` (see [`demo-config.md`](demo-config.md)) — no Compose init job. The API bind-mounts the same tree read-only at `/data` with `GEOAICUBES_STORAGE__DISCOVERY_MODE=filesystem` and `LOCAL_ROOT=/data/GEODATACUBE_ZARR_openEO` so inventory and TiTiler read on-disk Zarrs without byte copy.

After `make up-d`, open the viewer at http://localhost:5173; it calls `GET /api/v1/inventory/zarr` and loads tiles from the API origin only.

## CLI smoke

```bash
uv run geoaicubes ok
```

## Workflow UI test

Keep the stack running, then run Cursor `/test` (see `tests/e2e/README.md`).