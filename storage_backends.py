import os, json
from pathlib import Path

# Optional deps
try:
    import boto3
    from botocore.config import Config as BotoConfig
except Exception:
    boto3 = None; BotoConfig = None

try:
    from google.cloud import storage as gcs_storage
except Exception:
    gcs_storage = None

class StorageBackend:
    def write_text(self, path: str, text: str): raise NotImplementedError

class LocalStorage(StorageBackend):
    def write_text(self, path: str, text: str):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

class S3Storage(StorageBackend):
    def __init__(self, bucket: str, prefix: str = "", region: str = None):
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self.region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
        self._client = boto3.client("s3", region_name=self.region,
                                    config=BotoConfig(retries={"max_attempts":3,"mode":"standard"})) if boto3 else None

    def write_text(self, path: str, text: str):
        key = f"{self.prefix}/{Path(path).name}" if self.prefix else Path(path).name
        if self._client:
            self._client.put_object(Bucket=self.bucket, Key=key, Body=text.encode("utf-8"), ContentType="application/json")
        # mirror locally for debugging
        mirror = Path(f"/mnt/data/s3_mirror/{self.bucket}/{key}")
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(text, encoding="utf-8")

class GCSStorage(StorageBackend):
    def __init__(self, bucket: str, prefix: str = ""):
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self._client = gcs_storage.Client() if gcs_storage else None
        self._bucket = self._client.bucket(self.bucket) if self._client else None

    def write_text(self, path: str, text: str):
        key = f"{self.prefix}/{Path(path).name}" if self.prefix else Path(path).name
        if self._bucket:
            blob = self._bucket.blob(key)
            blob.upload_from_string(text, content_type="application/json")
        # mirror locally for debugging
        mirror = Path(f"/mnt/data/gcs_mirror/{self.bucket}/{key}")
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(text, encoding="utf-8")

def select_backend() -> StorageBackend:
    backend = os.getenv("SAMF_STORAGE_BACKEND","local").lower()
    if backend == "s3":
        return S3Storage(os.getenv("SAMF_S3_BUCKET","samf-demo"), os.getenv("SAMF_S3_PREFIX","incidents"))
    if backend == "gcs":
        return GCSStorage(os.getenv("SAMF_GCS_BUCKET","samf-demo"), os.getenv("SAMF_GCS_PREFIX","incidents"))
    return LocalStorage()
