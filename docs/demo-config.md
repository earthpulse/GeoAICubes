# Demo configuration

Runtime settings for the GeoAICubes stack (Step 0–1). **Authoritative for code:** `src/geoaicubes/config.py` (`StorageSettings` via `GEOAICUBES_STORAGE__*` env). **Secrets:** use env or a local `.env` (never commit). Demo AOI, dates, bands, and class map: document in this file when ICGC confirms (**G1**); until then see [`program/preflight-log.md`](program/preflight-log.md).

## Storage and discovery

| Concern | Native dev (`make api` / `make ui`) | Docker Compose (`make up-d`) |
|---------|--------------------------------------|------------------------------|
| Discovery | `GEOAICUBES_STORAGE__DISCOVERY_MODE=filesystem` | API container: `filesystem` with `LOCAL_ROOT=/data/GEODATACUBE_ZARR_openEO` |
| Zarr tree on disk | Repo `data/GEODATACUBE_ZARR_openEO/` | Same tree bind-mounted read-only at `/data` in `api` |
| S3 / MinIO | Optional: `make minio-up`, set `discovery_mode=s3` | MinIO service on :9000; bucket `data` over host `data/` |

### Env keys (`config/.env.example`)

Copy to repo-root `.env` or export before `make api`:

| Variable | Role |
|----------|------|
| `GEOAICUBES_STORAGE__DISCOVERY_MODE` | `filesystem` or `s3` |
| `GEOAICUBES_STORAGE__LOCAL_ROOT` | Host path to Zarr prefix (default `data/GEODATACUBE_ZARR_openEO`) |
| `GEOAICUBES_STORAGE__ENDPOINT_URL` | MinIO S3 endpoint (native: `http://localhost:9000`) |
| `GEOAICUBES_STORAGE__BUCKET` | Bucket name (default `data`) |
| `GEOAICUBES_STORAGE__PREFIX` | Key prefix inside bucket (`GEODATACUBE_ZARR_openEO`) |
| `GEOAICUBES_STORAGE__ACCESS_KEY_ID` / `SECRET_ACCESS_KEY` | MinIO credentials (dev defaults in example file) |
| `MINIO_*` | Compose MinIO root user/password and console redirect |

**URI mapping (S3 mode):** store `Geodatacube_orto2024.zarr` → `s3://{bucket}/{prefix}/Geodatacube_orto2024.zarr/` (see `StorageSettings.store_s3_uri`).

**Inventory path (filesystem mode):** relative `path` field uses `store_host_path` under `LOCAL_ROOT`.

### MinIO in-place layout

Compose mounts host `data/` into MinIO at `/data` (`server /data`). No byte-copy init job: Zarr stores live directly under `data/GEODATACUBE_ZARR_openEO/`. Console: http://localhost:9001 (credentials in `config/.env.example`).

## API, CORS, viewer

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEOAICUBES_API_PORT` | `8000` | Uvicorn port for `make api` |
| `GEOAICUBES_CORS_ORIGINS` | `http://localhost:5173,...` | FastAPI CORS allowlist |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Viewer fetch origin (build-time in Compose image) |

## Logging (CLI, API, library)

Shared helper: `geoaicubes.logging_config`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEOAICUBES_LOG_LEVEL` | `INFO` | Root log level (`DEBUG`, `WARNING`, …) |

Format (stderr): `YYYY-MM-DD HH:MM:SS | LEVEL | logger.name | message`. CLI and API call `configure_logging()` at startup.

## Related

- Runbook: [`scaffold.md`](scaffold.md)
- Inventory + tiles: [`data-plane/inventory-schema.md`](data-plane/inventory-schema.md), [`data-plane/titiler-integration.md`](data-plane/titiler-integration.md)
- Parallel preflight: [`program/preflight-log.md`](program/preflight-log.md)