from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MinioStorage(S3Boto3Storage):
    bucket_name = settings.MINIO_BUCKET_NAME
    endpoint_url = settings.MINIO_ENDPOINT_URL
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    region_name = settings.MINIO_REGION_NAME
    default_acl = None
    file_overwrite = False
    querystring_auth = True
    # Signed URL lifetime in seconds (1 hour). Bucket must be created manually or via deploy script.
    querystring_expire = 3600