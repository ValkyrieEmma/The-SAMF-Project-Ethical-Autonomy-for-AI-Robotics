# SAMF v5.5


## Storage Backends
Set `SAMF_STORAGE_BACKEND=local|s3|gcs` and (if s3/gcs) also:
- S3: `SAMF_S3_BUCKET`, optional `SAMF_S3_PREFIX`, `AWS_REGION`
- GCS: `SAMF_GCS_BUCKET`, optional `SAMF_GCS_PREFIX`

Incident reports are saved locally and mirrored to the configured backend.


## Quick Credentials Checklist
- **Local only**: No creds needed; logs & incidents store under `/mnt/data`.
- **S3 mirroring**: Set `SAMF_STORAGE_BACKEND=s3`, `SAMF_S3_BUCKET`, optional `SAMF_S3_PREFIX`, `AWS_REGION` (or rely on AWS default env/roles).
- **GCS mirroring**: Set `SAMF_STORAGE_BACKEND=gcs`, `SAMF_GCS_BUCKET`, optional `SAMF_GCS_PREFIX`. Provide GCP auth via `GOOGLE_APPLICATION_CREDENTIALS`.
- **Slack alerts**: Set `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...` (optional).

### Example `.env`
```
SAMF_STORAGE_BACKEND=s3
SAMF_S3_BUCKET=my-samf-bucket
SAMF_S3_PREFIX=incidents/prod
AWS_REGION=us-east-1

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XYZ
SAMF_DECISIONS_LOG=/mnt/data/samf_logs/decisions.jsonl
SAMF_ANON_SALT=change_me
```

## Health Check
Run a quick probe to confirm integrations:
```python
from core.health_check import overall_health
print(overall_health())  # => {'s3': True/False, 'gcs': True/False, 'slack': True/False}
```
