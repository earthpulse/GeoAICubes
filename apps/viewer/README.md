# GeoAICubes viewer

Step 0 Svelte shell under `apps/viewer/`. The UI talks to the API only (`GET {VITE_API_BASE_URL}/health` on mount).

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