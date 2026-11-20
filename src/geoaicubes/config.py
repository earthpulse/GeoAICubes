"""Storage and demo path settings (Step 1 I1)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DiscoveryMode = Literal["filesystem", "s3"]


def project_root() -> Path:
    """Repo root (directory containing pyproject.toml)."""
    here = Path(__file__).resolve().parent
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


class StorageSettings(BaseSettings):
    """MinIO / S3 layout shared by inventory, TiTiler, and GDAL readers."""

    model_config = SettingsConfigDict(
        env_prefix="GEOAICUBES_STORAGE__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    endpoint_url: str = Field(default="http://localhost:9000")
    bucket: str = Field(default="data")
    prefix: str = Field(default="GEODATACUBE_ZARR_openEO")
    access_key_id: str = Field(default="")
    secret_access_key: str = Field(default="")
    region: str = Field(default="us-east-1")
    use_ssl: bool = Field(default=False)
    discovery_mode: DiscoveryMode = Field(default="filesystem")
    local_root: Path = Field(default=Path("data/GEODATACUBE_ZARR_openEO"))

    @field_validator("local_root", mode="before")
    @classmethod
    def _coerce_local_root(cls, v: object) -> Path:
        if isinstance(v, Path):
            return v
        return Path(str(v))

    @field_validator("access_key_id", mode="before")
    @classmethod
    def _default_access_key(cls, v: object) -> str:
        if v:
            return str(v)
        return os.environ.get("MINIO_ROOT_USER", "geoaicubes")

    @field_validator("secret_access_key", mode="before")
    @classmethod
    def _default_secret(cls, v: object) -> str:
        if v:
            return str(v)
        return os.environ.get("MINIO_ROOT_PASSWORD", "geoaicubes-dev-only")

    @field_validator("prefix", mode="after")
    @classmethod
    def _strip_prefix(cls, v: str) -> str:
        return v.strip("/")

    def local_zarr_root(self) -> Path:
        """Absolute host path to the Zarr tree (native dev)."""
        root = self.local_root
        if not root.is_absolute():
            root = project_root() / root
        return root.resolve()

    def store_s3_uri(self, store_id: str) -> str:
        """Canonical s3:// URI (Compose + TiTiler query ?url=)."""
        return f"s3://{self.bucket}/{self.prefix}/{store_id}/"

    def store_host_path(self, store_id: str) -> str:
        """Repo-relative path for inventory `path` in native dev."""
        return f"{self.local_root.as_posix().rstrip('/')}/{store_id}/"

    def store_open_target(self, store_id: str) -> str | Path:
        """Path or URI used by xarray.open_zarr for the active discovery mode."""
        if self.discovery_mode == "s3":
            return self.store_s3_uri(store_id)
        return self.local_zarr_root() / store_id


@lru_cache(maxsize=1)
def get_storage_settings() -> StorageSettings:
    return StorageSettings()
