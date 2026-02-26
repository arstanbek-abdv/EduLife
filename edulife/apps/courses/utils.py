from urllib.parse import urlparse
from datetime import timedelta
from django.conf import settings
from minio import Minio
from minio.error import S3Error


def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )


def ensure_bucket(client, bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def remove_object_if_exists(client, bucket_name, object_name):
    try:
        client.remove_object(bucket_name, object_name)
    except S3Error as exc:
        if exc.code not in {"NoSuchKey", "NoSuchObject"}:
            raise


def normalize_clickable_url(url: str) -> str:
    """
    Ensure URL is fully qualified (scheme + netloc), so UIs render it clickable.
    """
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url
    scheme = "https" if getattr(settings, "MINIO_USE_SSL", False) else "http"
    endpoint = getattr(settings, "MINIO_ENDPOINT", "").strip().lstrip("/")
    path = url if url.startswith("/") else f"/{url}"
    if endpoint:
        return f"{scheme}://{endpoint}{path}"
    return f"{scheme}://{path.lstrip('/')}"
