# GeoAICubes

ICGC GeoDataCubes and related [datacloud](https://datacloud.icgc.cat/datacloud/) assets.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (macOS/Linux example):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create the virtualenv and install the project (no runtime deps yet; ready for notebooks and libs later):

```bash
uv sync
```

## Download data

List or sync remote IIS listings (resume, unzip `.zip`, skip finished work). Full detail: [docs/data-download.md](docs/data-download.md).

```bash
make help
make list-geodatacubes      # preview GeoDataCubes
make sync-geodatacubes      # download + unzip → data/
make list-cobertes
make sync-cobertes          # → data/cobertes-sol/tif_unzip/
```

GeoDataCubes source: https://datacloud.icgc.cat/datacloud/geodatacubes/