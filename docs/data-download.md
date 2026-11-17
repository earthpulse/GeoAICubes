# Downloading ICGC datacloud data

GeoAICubes ships a small CLI that mirrors [IIS directory listings](https://datacloud.icgc.cat/datacloud/) into a local folder. It supports resume, automatic unzip for archives, and skipping work that is already finished.

Script: `scripts/fetch_datacloud.py`

## Requirements

- [uv](https://docs.astral.sh/uv/) and Python 3.12+ (`uv sync` from the repo root)
- Enough disk space for the datasets you select (GeoDataCubes alone is on the order of tens of GB)

The fetch CLI uses the Python stdlib only (no extra packages in `pyproject.toml` yet). Downloaded content is written under `data/` by default (see `.gitignore`).

## Commands

### `list`

Shows every file under a listing URL, remote size, type (`file` or `zip`), and local status at `--dest`:

| Status | Meaning |
|--------|---------|
| `ready` | File present, or zip fully extracted (marker written) |
| `download_needed` | Not on disk yet |
| `download_partial` | Incomplete download (resumed on next `sync`) |
| `extract_needed` | Zip complete; extraction not finished |
| `extract_partial` | Extraction started or interrupted |
| `unavailable` | Listed on the index page but HEAD returns 404 (skipped on `sync`) |

```bash
uv run python scripts/fetch_datacloud.py list "<URL>" --dest data
```

### `sync`

Downloads missing or partial files, resumes with HTTP `Range` when possible, extracts `.zip` archives, deletes the zip after a successful extract, and skips items already `ready`.

```bash
uv run python scripts/fetch_datacloud.py sync "<URL>" --dest data
```

Options:

- `--timeout SECONDS` — HTTP timeout (default: 120)
- `--no-resume` — discard partial downloads and fetch again from byte 0

If one remote file fails (for example HTTP 404), `sync` continues with the rest and exits with code 1 if anything failed. Re-run `sync` to retry.

### Zip handling

- `something.zarr.zip` is extracted to `something.zarr/` under the same relative path.
- Completion is recorded in `something.zarr/.extracted` (JSON with zip size and member count).
- If the zip is present but extraction is incomplete, only extraction is retried.
- If the zip is partial, download resumes, then extraction runs.

Plain files (`.tif`, `.gpkg`, `.html`, etc.) are stored as-is with no unzip step.

## Example sources

| Dataset | URL | Suggested `--dest` |
|---------|-----|-------------------|
| GeoDataCubes | https://datacloud.icgc.cat/datacloud/geodatacubes/ | `data` |
| Cobertes de sòl (GeoTIFF) | https://datacloud.icgc.cat/datacloud/cobertes-sol/tif_unzip/ | `data/cobertes-sol/tif_unzip` |

After unzip, ZARR cubes are directories (for example `Geodatacube_orto2024.zarr/`). The notebook in the GeoDataCubes folder expects paths to those extracted ZARR trees.

## Makefile shortcuts

After `uv sync`, run from the repo root. Targets use `uv run python` by default (`PYTHON` in the Makefile).

```bash
make help
make list-geodatacubes
make sync-geodatacubes
make list-cobertes
make sync-cobertes
```

Generic invocations:

```bash
make list URL="https://…/" DEST=data/custom
make sync URL="https://…/" DEST=data/custom TIMEOUT=300
```

## Legacy entry point

`scripts/download_geodatacubes.py` forwards to `fetch_datacloud.py` for older instructions; prefer `fetch_datacloud.py` or the Makefile targets.