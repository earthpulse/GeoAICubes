# Demo configuration (provisional)

Single source of truth for the demo will be **`config/demo.yaml`** plus environment overrides (AOI, dates, class map). **Step 1 storage** is already loaded from env via `StorageSettings` in `src/geoaicubes/config.py` (`GEOAICUBES_STORAGE__*`). Values stay provisional until ICGC confirms AOI, dates, bands, and class map.

## Environment template

`config/.env.example` lists Compose and local dev variables:

- **MinIO (Compose):** `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET`, `MINIO_BROWSER_REDIRECT_URL`
- **Storage (library / API):** `GEOAICUBES_STORAGE__*` (nested settings; see below)
- **API:** `GEOAICUBES_API_PORT`, `GEOAICUBES_CORS_ORIGINS`
- **Viewer build:** `VITE_API_BASE_URL`

## MinIO in-place layout (Step 1)

GeoDataCube Zarr stores live on the host under the repo `data/` tree. Step 1 exposes them through MinIO **without copying cube bytes** into a separate MinIO-only directory.

| Layer | Path |
|-------|------|
| Host (authoritative) | `<repo>/data/GEODATACUBE_ZARR_openEO/<store>.zarr/` |
| S3 bucket | `data` (agreed demo bucket name; override via env) |
| Object key prefix | `GEODATACUBE_ZARR_openEO/` |
| Example S3 URI | `s3://data/GEODATACUBE_ZARR_openEO/Geodatacube_orto2024.zarr/` |

### Host path ↔ `s3://` mapping

Treat the prefix as the stable join between filesystem layout and S3 keys:

```text
<repo>/data/GEODATACUBE_ZARR_openEO/<relative...>
  ↔  s3://data/GEODATACUBE_ZARR_openEO/<relative...>
```

Examples:

| Host path | S3 URI |
|-----------|--------|
| `data/GEODATACUBE_ZARR_openEO/Geodatacube_orto2024.zarr/` | `s3://data/GEODATACUBE_ZARR_openEO/Geodatacube_orto2024.zarr/` |
| `data/GEODATACUBE_ZARR_openEO/GeoDataCube_cobertes-sol-v1r0-2023.zarr/` | `s3://data/GEODATACUBE_ZARR_openEO/GeoDataCube_cobertes-sol-v1r0-2023.zarr/` |

Local tools may still open the host path directly (e.g. `xarray.open_zarr("data/GEODATACUBE_ZARR_openEO/...")`). In Compose, the API, TiTiler, and inventory code use the same logical tree via `GEOAICUBES_STORAGE__*` and the URIs above.

**TiTiler integration (Step 1):** Zarr tiles are served from the **API** process (`titiler-xarray` mount at `/tiles/zarr`), not a separate Compose service. Tile query parameters (`url`, `variable`, `rescale`, optional time via `sel` / inventory `time_index`) are defined in [`data-plane/titiler-integration.md`](data-plane/titiler-integration.md).

### Compose in-place volumes (`deploy/docker-compose.yml`)

MinIO and the API share the host Zarr tree via bind mounts (no duplicate cube directory under `data/minio/`):

| Service | Volume | Effect |
|---------|--------|--------|
| `minio` | `../data:/data` | MinIO metadata and buckets live under repo `data/` |
| `api` | `../data:/data:ro` | Same host paths as inventory `path` fields; Compose uses `DISCOVERY_MODE=filesystem` on this mount (inventory `uri` still documents logical `s3://…`) |

MinIO may create `.minio.sys/` and a bucket directory under `<repo>/data/`. Do not migrate with `mc cp` / `mc mirror` for full Zarr trees. A narrower MinIO mount (`../data/GEODATACUBE_ZARR_openEO` only) is acceptable if URIs still use prefix `GEODATACUBE_ZARR_openEO/`.

### MinIO buckets (optional)

Compose starts MinIO with `server /data` on the bind-mounted repo `data/` folder — no init container. Step 1 inventory and tiles do **not** require an S3 bucket object layout.

If you want to exercise S3 clients against MinIO, create a bucket from the console (:9001) or with [mc](https://github.com/minio/mc) on the host (`make minio-up` first):

```bash
mc alias set geoaicubes http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing geoaicubes/data
```

Do not `mc cp` / `mc mirror` full Zarr trees when the cubes already live on disk.

`MINIO_BUCKET` in `.env` must match the storage bucket (`data` by default). In **Compose**, the API uses `GEOAICUBES_STORAGE__DISCOVERY_MODE=filesystem` and `GEOAICUBES_STORAGE__LOCAL_ROOT=/data/GEODATACUBE_ZARR_openEO` so inventory lists on-disk Zarrs without `mc` upload; TiTiler `?url=` uses container filesystem paths. Set `DISCOVERY_MODE=s3` only when objects are actually registered under the bucket prefix (optional later S3-only path).

## `GEOAICUBES_STORAGE__*` keys

The Python config loader (`src/geoaicubes/config.py`, Step 1) reads nested env vars (double underscore). Defaults align with local Compose MinIO.

| Variable | Purpose | Local / Compose default |
|----------|---------|------------------------|
| `GEOAICUBES_STORAGE__ENDPOINT_URL` | S3 API base URL | `http://localhost:9000` |
| `GEOAICUBES_STORAGE__BUCKET` | Bucket name | `data` |
| `GEOAICUBES_STORAGE__PREFIX` | Key prefix under bucket (no leading `s3://`) | `GEODATACUBE_ZARR_openEO` |
| `GEOAICUBES_STORAGE__ACCESS_KEY_ID` | S3 access key | same as `MINIO_ROOT_USER` |
| `GEOAICUBES_STORAGE__SECRET_ACCESS_KEY` | S3 secret key | same as `MINIO_ROOT_PASSWORD` |
| `GEOAICUBES_STORAGE__REGION` | SigV4 region (MinIO accepts any) | `us-east-1` |
| `GEOAICUBES_STORAGE__USE_SSL` | HTTPS to endpoint | `false` |
| `GEOAICUBES_STORAGE__DISCOVERY_MODE` | How stores are listed and opened | `filesystem` (native `make api`); Compose API sets `s3` |
| `GEOAICUBES_STORAGE__LOCAL_ROOT` | Host directory for `filesystem` discovery (repo-relative OK) | `data/GEODATACUBE_ZARR_openEO` |

Helper: a store name `Geodatacube_orto2024.zarr` resolves to URI  
`s3://{BUCKET}/{PREFIX}/Geodatacube_orto2024.zarr/` using the env values above (`StorageSettings.store_s3_uri`).

### Discovery mode (`filesystem` vs `s3`)

| Mode | Typical use | Listing | Inventory `path` | TiTiler `?url=` in templates |
|------|-------------|---------|------------------|--------------------------------|
| `filesystem` | `make api` without Compose | Scans `LOCAL_ROOT` for `*.zarr/` | Repo-relative host path under `LOCAL_ROOT` | Absolute host path (resolved under repo) |
| `s3` | Compose `api` service (and native dev with `make minio-up`) | Lists `s3://{BUCKET}/{PREFIX}/` | Same as canonical `uri` (`s3://…`) | Percent-encoded `s3://{BUCKET}/{PREFIX}/{store}/` |

Inventory always includes a canonical **`uri`** (`s3://…`) for each store. With `discovery_mode=s3`, GDAL/S3 env is applied at API startup (`apply_s3_env`) so TiTiler and `xarray` use the same MinIO endpoint and credentials as inventory I/O.

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

`config/demo.yaml` will hold bbox, cube paths, label paths, date ranges, and class mapping. Not checked in yet; wire into the same config module when ICGC freezes demo parameters (storage env above is already live for Step 1).