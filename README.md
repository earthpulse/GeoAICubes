# GeoAICubes

ICGC GeoDataCubes and related [datacloud](https://datacloud.icgc.cat/datacloud/) assets.

## Project layout

| Path | Purpose |
|------|---------|
| `src/geoaicubes/` | Python library (shared by notebooks, API, exports, benchmarks) |
| `config/` | Env template (`config/.env.example`); optional `inventory-export.json` snapshot |
| `deploy/` | Docker Compose and deployment assets |
| `apps/viewer/` | Web viewer UI (talks to the API only) |
| `tests/` | `pytest` (`integration/`, `unit/`) and e2e UI catalog (`e2e/`, Cursor `/test`) |
| `references/` | Plec scope and roadmap (markdown + PDFs) |
| `data/` | Downloaded datasets (gitignored) |

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (macOS/Linux example):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

Quality checks (also on GitHub Actions for `main` / PRs):

```bash
make check
```

## Local stack

```bash
make help
make api          # FastAPI on :8000
make ui           # Vite viewer on :5173 (bun install in apps/viewer first)
make up-d         # API + UI + MinIO in Docker
```

| Service | Command | URL |
|---------|---------|-----|
| API | `make api` | http://localhost:8000/health · OpenAPI http://localhost:8000/docs |
| Inventory | (API up) | `GET /api/v1/inventory/zarr` |
| Tiles | (API up) | `/tiles/zarr/tiles/WebMercatorQuad/{z}/{x}/{y}.png?...` |
| Viewer | `make ui` | http://localhost:5173 |
| MinIO (optional) | `make minio-up` | S3 :9000, console :9001 |

Compose: `deploy/docker-compose.yml` with env template `config/.env.example`.

### Storage (Step 1)

Runtime settings: `src/geoaicubes/config.py` (`StorageSettings`, env prefix `GEOAICUBES_STORAGE__`). Copy `config/.env.example` to a local `.env` (never commit secrets).

| Mode | `GEOAICUBES_STORAGE__DISCOVERY_MODE` | Zarr root |
|------|--------------------------------------|-----------|
| Native dev | `filesystem` (default) | `data/GEODATACUBE_ZARR_openEO/` under repo |
| S3 / MinIO | `s3` | `s3://{bucket}/{prefix}/{store}.zarr/` |

MinIO in Compose bind-mounts host `data/` in-place (no byte-copy init). API container uses `LOCAL_ROOT=/data/GEODATACUBE_ZARR_openEO` when configured for filesystem discovery.

### Logging

`GEOAICUBES_LOG_LEVEL` (default `INFO`) — shared format via `geoaicubes.logging_config` for CLI and API.

### Inventory snapshot

```bash
make inventory-export   # writes config/inventory-export.json (API must be up for live fetch)
```

GeoDataCubes source: https://datacloud.icgc.cat/datacloud/geodatacubes/