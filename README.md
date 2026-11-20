# GeoAICubes

ICGC GeoDataCubes and related [datacloud](https://datacloud.icgc.cat/datacloud/) assets.

## Project layout

| Path | Purpose |
|------|---------|
| `src/geoaicubes/` | Python library (shared by notebooks, API, exports, benchmarks) |
| `config/` | Demo and runtime configuration (YAML/TOML; secrets via env, not in repo) |
| `deploy/` | Docker Compose and deployment assets |
| `apps/viewer/` | Web viewer UI (talks to the API only) |
| `docs/` | Runbooks and config notes (`docs/scaffold.md`, `docs/demo-config.md`) |
| `tests/` | `pytest` smoke tests and UI workflow catalog |
| `data/` | Downloaded datasets (gitignored) |

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (macOS/Linux example):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install the project and dev tools (Ruff, pytest, httpx):

```bash
uv sync
```

Run lint, format check, and tests (also on GitHub Actions for `main` / PRs):

```bash
make check
```

## Local stack

Quick reference — full port matrix and Compose notes: [docs/scaffold.md](docs/scaffold.md).

```bash
make help
make api          # FastAPI on :8000
make ui           # Vite viewer on :5173 (bun install in apps/viewer first)
make up-d         # API + UI + MinIO in Docker
```

Demo env keys and logging: [docs/demo-config.md](docs/demo-config.md).

GeoDataCubes source: https://datacloud.icgc.cat/datacloud/geodatacubes/