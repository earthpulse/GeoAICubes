"""Demo configuration contract — single loader for YAML/TOML plus env overrides."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_ENV_PREFIX = "GEOAICUBES_"
_DEFAULT_DEMO_REL = Path("config") / "demo.yaml"


def _repo_root() -> Path:
    """Project root (directory that contains ``config/`` and ``src/``)."""
    here = Path(__file__).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "config").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[1]


def default_demo_config_path() -> Path:
    """Default path to the demo YAML/TOML file."""
    return _repo_root() / _DEFAULT_DEMO_REL


class BboxConfig(BaseModel):
    """Area of interest as a WGS84 bounding box (decimal degrees)."""

    min_lon: float = Field(description="Western edge (min longitude).")
    min_lat: float = Field(description="Southern edge (min latitude).")
    max_lon: float = Field(description="Eastern edge (max longitude).")
    max_lat: float = Field(description="Northern edge (max latitude).")


class DateRangeConfig(BaseModel):
    """Inclusive demo period for cube time steps (ISO 8601 dates)."""

    start: str = Field(description="Start date (YYYY-MM-DD).")
    end: str = Field(description="End date (YYYY-MM-DD).")


class DataPathsConfig(BaseModel):
    """Filesystem paths to local cubes and labels (under ``data_root`` when relative)."""

    data_root: Path = Field(
        default=Path("data"),
        description="Root for downloaded / generated assets (gitignored).",
    )
    cube_zarr: str = Field(
        description="Path to the demo Zarr cube (relative to data_root or absolute)."
    )
    label_raster: str = Field(
        description="Path to reference labels (GeoTIFF or similar) for training/demo."
    )
    classification_output: str | None = Field(
        default=None,
        description="Optional path for precomputed classification rasters.",
    )
    change_map_output: str | None = Field(
        default=None,
        description="Optional path for precomputed change-detection output.",
    )


class ClassEntry(BaseModel):
    """One land-cover or thematic class in the demo legend."""

    id: int = Field(ge=0, description="Integer class id stored in rasters.")
    name: str = Field(description="Human-readable class label.")
    color: str | None = Field(
        default=None,
        description="Optional hex color for viewer symbology (e.g. #228822).",
    )


class S3StorageConfig(BaseModel):
    """S3-compatible object storage (local MinIO or remote bucket) for published assets."""

    endpoint_url: str = Field(
        description="S3 API endpoint (e.g. http://localhost:9000 for MinIO)."
    )
    bucket: str = Field(description="Bucket name for demo assets.")
    prefix: str = Field(
        default="",
        description="Key prefix inside the bucket (no leading slash).",
    )
    region: str | None = Field(
        default=None,
        description="Optional region name for signing (MinIO often uses us-east-1).",
    )
    use_ssl: bool = Field(default=False, description="Whether to use HTTPS to reach endpoint.")
    access_key_id: SecretStr | None = Field(
        default=None,
        description="Credential from env only — not set in committed YAML.",
    )
    secret_access_key: SecretStr | None = Field(
        default=None,
        description="Credential from env only — not set in committed YAML.",
    )


class DemoConfig(BaseSettings):
    """
    Single source of truth for the GeoAICubes demo: AOI, dates, paths, classes, storage.

    Load via :func:`load_demo_config`. Values in ``config/demo.yaml`` are the baseline;
    environment variables prefixed with ``GEOAICUBES_`` override (nested keys use ``__``,
    e.g. ``GEOAICUBES_BBOX__MIN_LON``).
    """

    model_config = SettingsConfigDict(
        env_prefix=_ENV_PREFIX,
        env_nested_delimiter="__",
        extra="ignore",
    )

    name: str = Field(default="geoaicubes-demo", description="Demo dataset / run label.")
    crs: str = Field(
        default="EPSG:4326",
        description="CRS for bbox and API export metadata (processing CRS may differ).",
    )
    bbox: BboxConfig
    dates: DateRangeConfig
    paths: DataPathsConfig
    classes: list[ClassEntry] = Field(
        min_length=1,
        description="Ordered class legend for RF/DL demo and viewer.",
    )
    storage: S3StorageConfig
    api_base_url: str | None = Field(
        default=None,
        description="Optional public API base URL (viewer); override via GEOAICUBES_API_BASE_URL.",
    )

    @field_validator("classes")
    @classmethod
    def _unique_class_ids(cls, entries: list[ClassEntry]) -> list[ClassEntry]:
        ids = [e.id for e in entries]
        if len(ids) != len(set(ids)):
            msg = "Class ids must be unique"
            raise ValueError(msg)
        return entries

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # First matching source wins: init kwargs, then env, then file baseline.
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            _YamlSettingsSource(settings_cls),
            file_secret_settings,
        )


_yaml_path_ctx: Path | None = None


def _set_yaml_path(path: Path) -> None:
    global _yaml_path_ctx
    _yaml_path_ctx = path


def _current_yaml_path() -> Path:
    if _yaml_path_ctx is not None:
        return _yaml_path_ctx
    return default_demo_config_path()


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        msg = f"Demo config file not found: {path}"
        raise FileNotFoundError(msg)
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".toml":
        data = tomllib.loads(text)
    else:
        msg = f"Unsupported demo config format (use .yaml, .yml, or .toml): {path}"
        raise ValueError(msg)
    if not isinstance(data, dict):
        msg = f"Demo config root must be a mapping: {path}"
        raise TypeError(msg)
    return data


class _YamlSettingsSource(PydanticBaseSettingsSource):
    """Loads nested demo fields from the YAML/TOML file (lowest priority among sources)."""

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        return None, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        path = _current_yaml_path()
        try:
            return _read_config_file(path)
        except FileNotFoundError:
            return {}


def load_demo_config(path: Path | str | None = None) -> DemoConfig:
    """
    Load demo configuration from ``path`` (default ``config/demo.yaml``) with env overrides.

    Parameters
    ----------
    path:
        Optional path to a YAML or TOML file under ``config/``. When omitted, uses the
        repository default ``config/demo.yaml``.

    Returns
    -------
    DemoConfig
        Validated settings instance.
    """
    resolved = Path(path) if path is not None else default_demo_config_path()
    resolved = resolved.expanduser()
    if not resolved.is_absolute():
        resolved = (_repo_root() / resolved).resolve()

    prev = _yaml_path_ctx
    _set_yaml_path(resolved)
    try:
        return DemoConfig()
    finally:
        _set_yaml_path(prev) if prev is not None else _clear_yaml_path()


def _clear_yaml_path() -> None:
    global _yaml_path_ctx
    _yaml_path_ctx = None


@lru_cache(maxsize=1)
def get_demo_config() -> DemoConfig:
    """Cached load of the default demo config (respects env at first call)."""
    return load_demo_config()


def clear_demo_config_cache() -> None:
    """Clear :func:`get_demo_config` cache (for tests)."""
    get_demo_config.cache_clear()