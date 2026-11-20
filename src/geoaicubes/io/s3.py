"""S3 / MinIO client wiring (Step 1 I3)."""

from __future__ import annotations

import os

import s3fs

from geoaicubes.config import StorageSettings, get_storage_settings

_DEFAULT_FS: s3fs.S3FileSystem | None = None


def get_s3_filesystem(settings: StorageSettings | None = None) -> s3fs.S3FileSystem:
    """Shared s3fs client — same bucket/prefix layout as TiTiler ?url= s3:// URIs."""
    global _DEFAULT_FS
    cfg = settings or get_storage_settings()
    if settings is None and _DEFAULT_FS is not None:
        return _DEFAULT_FS
    fs = s3fs.S3FileSystem(
        key=cfg.access_key_id,
        secret=cfg.secret_access_key,
        client_kwargs={
            "endpoint_url": cfg.endpoint_url,
            "region_name": cfg.region,
        },
        config_kwargs={"s3": {"addressing_style": "path"}},
        use_ssl=cfg.use_ssl,
    )
    if settings is None:
        _DEFAULT_FS = fs
    return fs


def apply_s3_env(settings: StorageSettings | None = None) -> None:
    """Align process env with GDAL/rasterio S3 access (TiTiler mount)."""
    cfg = settings or get_storage_settings()
    os.environ.setdefault("AWS_ACCESS_KEY_ID", cfg.access_key_id)
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", cfg.secret_access_key)
    os.environ.setdefault("AWS_DEFAULT_REGION", cfg.region)
    os.environ.setdefault("AWS_S3_ENDPOINT", cfg.endpoint_url)
    os.environ.setdefault("AWS_ENDPOINT_URL", cfg.endpoint_url)
    os.environ.setdefault("AWS_VIRTUAL_HOSTING", "FALSE")
    if not cfg.use_ssl:
        os.environ.setdefault("AWS_HTTPS", "NO")
        os.environ.setdefault("AWS_NO_SIGN_REQUEST", "NO")


def zarr_mapper_for_uri(uri: str, settings: StorageSettings | None = None):
    """Fsspec mapper for an s3://…/*.zarr/ URI."""
    cfg = settings or get_storage_settings()
    apply_s3_env(cfg)
    fs = get_s3_filesystem(cfg)
    path = uri.removeprefix("s3://")
    return fs.get_mapper(path)
