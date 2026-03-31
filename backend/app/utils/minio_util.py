from __future__ import annotations

from functools import lru_cache
from pathlib import Path, PurePosixPath

from minio import Minio
from minio.error import S3Error

from app.config.setting import settings


def normalize_object_key(key: str) -> str:
    k = (key or "").strip()
    if not k:
        raise ValueError("empty key")
    if k.startswith("/"):
        k = k.lstrip("/")
    parts = [p for p in PurePosixPath(k).parts if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError("invalid key")
    return str(PurePosixPath(*parts))


@lru_cache
def get_minio_client() -> Minio:
    endpoint = settings.MINIO_ENDPOINT
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    if not endpoint or not access_key or not secret_key:
        raise ValueError("minio config missing")
    client = Minio(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=settings.MINIO_SECURE,
    )
    _ensure_bucket(client, settings.MINIO_BUCKET)
    return client


def upload_file_to_minio(file_path: Path, object_key: str, content_type: str | None = None) -> str:
    client = get_minio_client()
    key = normalize_object_key(object_key)
    client.fput_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=key,
        file_path=str(file_path),
        content_type=content_type,
    )
    return key


def remove_objects_from_minio(object_keys: list[str]) -> None:
    if not object_keys:
        return
    try:
        client = get_minio_client()
    except Exception:
        return
    for k in object_keys:
        try:
            client.remove_object(settings.MINIO_BUCKET, normalize_object_key(k))
        except Exception:
            continue


def _ensure_bucket(client: Minio, bucket: str) -> None:
    if not bucket:
        raise ValueError("empty bucket")
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error:
        raise
