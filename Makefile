PYTHON ?= uv run python
SCRIPT := scripts/fetch_datacloud.py
TIMEOUT ?= 120

GEODATACUBES_URL := https://datacloud.icgc.cat/datacloud/geodatacubes/
COBERTES_TIF_URL := https://datacloud.icgc.cat/datacloud/cobertes-sol/tif_unzip/

GEODATACUBES_DEST := data
COBERTES_DEST := data/cobertes-sol/tif_unzip

.PHONY: help list sync list-geodatacubes sync-geodatacubes list-cobertes sync-cobertes

help:
	@echo "GeoAICubes data fetch (see docs/data-download.md)"
	@echo ""
	@echo "  make list-geodatacubes     List GeoDataCubes remote files and local status"
	@echo "  make sync-geodatacubes     Download + unzip GeoDataCubes into $(GEODATACUBES_DEST)/"
	@echo "  make list-cobertes         List cobertes-sol GeoTIFF listing"
	@echo "  make sync-cobertes         Download cobertes-sol into $(COBERTES_DEST)/"
	@echo ""
	@echo "  make list URL=<url> DEST=<dir>   List any IIS directory"
	@echo "  make sync URL=<url> DEST=<dir>   Sync any IIS directory"
	@echo ""
	@echo "Optional: TIMEOUT=300  (requires: uv sync)"

list-geodatacubes:
	$(PYTHON) $(SCRIPT) list "$(GEODATACUBES_URL)" --dest $(GEODATACUBES_DEST) --timeout $(TIMEOUT)

sync-geodatacubes:
	$(PYTHON) $(SCRIPT) sync "$(GEODATACUBES_URL)" --dest $(GEODATACUBES_DEST) --timeout $(TIMEOUT)

list-cobertes:
	$(PYTHON) $(SCRIPT) list "$(COBERTES_TIF_URL)" --dest $(COBERTES_DEST) --timeout $(TIMEOUT)

sync-cobertes:
	$(PYTHON) $(SCRIPT) sync "$(COBERTES_TIF_URL)" --dest $(COBERTES_DEST) --timeout $(TIMEOUT)

list:
ifndef URL
	$(error Set URL=…, e.g. make list URL="$(GEODATACUBES_URL)" DEST=data)
endif
ifndef DEST
	$(error Set DEST=…, e.g. make list URL="$(GEODATACUBES_URL)" DEST=data)
endif
	$(PYTHON) $(SCRIPT) list "$(URL)" --dest $(DEST) --timeout $(TIMEOUT)

sync:
ifndef URL
	$(error Set URL=…, e.g. make sync URL="$(GEODATACUBES_URL)" DEST=data)
endif
ifndef DEST
	$(error Set DEST=…, e.g. make sync URL="$(GEODATACUBES_URL)" DEST=data)
endif
	$(PYTHON) $(SCRIPT) sync "$(URL)" --dest $(DEST) --timeout $(TIMEOUT)