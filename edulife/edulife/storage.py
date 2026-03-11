from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class R2Storage(S3Boto3Storage):
    """
    Cloudflare R2 (or any S3‑compatible) storage backend.

    Configuration is taken from R2_* settings with a fallback to legacy MINIO_* env vars.
    """

    bucket_name = settings.R2_BUCKET_NAME
    endpoint_url = settings.R2_ENDPOINT_URL
    access_key = settings.R2_ACCESS_KEY
    secret_key = settings.R2_SECRET_KEY
    region_name = settings.R2_REGION_NAME

    default_acl = None
    file_overwrite = False
    querystring_auth = True
    # Signed URL lifetime in seconds (1 hour).
    querystring_expire = 3600