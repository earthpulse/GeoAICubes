# Demo configuration (provisional)

Single source of truth for the demo will be **`config/demo.yaml`** plus environment overrides. Values stay provisional until ICGC confirms AOI, dates, bands, and class map.

## Environment template

`config/.env.example` lists Compose and local dev variables:

- **MinIO:** `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET`
- **API:** `GEOAICUBES_API_PORT`, `GEOAICUBES_CORS_ORIGINS`
- **Viewer build:** `VITE_API_BASE_URL`

When storage wiring lands, endpoint and bucket settings will use the `GEOAICUBES_STORAGE__*` prefix (see Makefile `minio-up` hint).

## Logging (CLI, API, library)

Shared setup: `geoaicubes.logging_config.configure_logging()`.

| Item | Value |
|------|--------|
| Stream | stderr |
| Format | `%(asctime)s \| %(levelname)s \| %(name)s \| %(message)s` |
| Date | `%Y-%m-%d %H:%M:%S` |
| Level | `GEOAICUBES_LOG_LEVEL` (default `INFO`; unknown values fall back to `INFO`) |

Used by the Typer CLI entry callback and the FastAPI app lifespan.

## YAML demo file (planned)

`config/demo.yaml` will hold bbox, cube paths, label paths, date ranges, and class mapping. Not checked in yet; add when the config loader (`src/geoaicubes/config.py`) is implemented.