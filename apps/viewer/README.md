# GeoAICubes viewer

Step 1 discovery viewer under `apps/viewer/`. The UI talks to the API only: `GET /health`, `GET /api/v1/inventory/zarr`, and TiTiler tile URLs from inventory templates (no Zarr/Xarray in the browser).

Layout: inventory-driven layers, map tiles from API `tile_url_template` only (see `src/geoaicubes/api/schemas/inventory.py`).

## Setup

```bash
cp .env.example .env   # optional; defaults to http://localhost:8000
bun install
```

## Commands

```bash
bun run dev      # Vite dev server (default :5173)
bun run build    # production bundle → dist/
bun run preview  # serve dist/
```

Set `VITE_API_BASE_URL` before `bun run build` when the API is not at `http://localhost:8000` (Compose uses build-time `ARG` in the UI image).

**Compose dev:** `deploy/docker-compose.yml` bind-mounts this directory into the UI service (Vite HMR). Rebuild the UI image only when `package.json` / `bun.lock` change; then `docker compose exec ui bun install` if needed.

## Workflow test

Terminal: **`make up`** · Cursor: **`/test`** (browser on http://localhost:5173/, one screenshot).

Optional without Docker: `make api` + `make ui`.

Python checks from repo root: **`make check`** (see repo `README.md`).