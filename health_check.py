import os

def s3_ok() -> bool:
    try:
        import boto3
    except Exception:
        return False
    try:
        bucket = os.getenv("SAMF_S3_BUCKET")
        if not bucket: return False
        s3 = boto3.client("s3")
        s3.head_bucket(Bucket=bucket)
        return True
    except Exception:
        return False

def gcs_ok() -> bool:
    try:
        from google.cloud import storage as gcs
    except Exception:
        return False
    try:
        bucket = os.getenv("SAMF_GCS_BUCKET")
        if not bucket: return False
        client = gcs.Client()
        b = client.bucket(bucket)
        _ = list(client.list_blobs(b, max_results=1))
        return True
    except Exception:
        return False

def slack_ok() -> bool:
    url = os.getenv("SLACK_WEBHOOK_URL")
    return bool(url and url.startswith("https://"))

def overall_health() -> dict:
    return {"s3": s3_ok(), "gcs": gcs_ok(), "slack": slack_ok()}
