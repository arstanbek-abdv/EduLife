from storages.backends.s3boto3 import S3Boto3Storage

class MinioStorage(S3Boto3Storage):
    bucket_name = "edulife"
    endpoint_url = "http://localhost:9000"
    access_key = "minioadmin"
    secret_key = "minioadmin123"
    region_name = "us-east-1"
    default_acl = None
    file_overwrite = False
    querystring_auth = True