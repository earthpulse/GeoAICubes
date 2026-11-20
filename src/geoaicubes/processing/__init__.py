"""Processing hooks — classification and change detection stubs (D2.2)."""

from __future__ import annotations

from typing import Any

from geoaicubes.config import DemoConfig

__all__ = ["run_change_map", "run_classification"]


def _stub_result(operation: str, **extra: Any) -> dict[str, Any]:
    return {
        "implementation": "stub",
        "operation": operation,
        "note": "No geospatial processing in Step 0 scaffold.",
        **extra,
    }


def run_classification(*, config: DemoConfig) -> dict[str, Any]:
    """Placeholder offline classification hook for CLI ``train`` and exports."""
    out = config.paths.classification_output
    return _stub_result(
        "run_classification",
        demo=config.name,
        output_path=str(out) if out else None,
    )


def run_change_map(*, config: DemoConfig) -> dict[str, Any]:
    """Placeholder change-map hook for downstream viewer layers."""
    out = config.paths.change_map_output
    return _stub_result(
        "run_change_map",
        demo=config.name,
        output_path=str(out) if out else None,
    )