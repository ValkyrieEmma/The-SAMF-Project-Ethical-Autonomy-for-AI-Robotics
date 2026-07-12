# ⚠️ DEFUNCT — This project is no longer maintained

**This repository is defunct and is not under active development.**

Development has moved to a new project for architectural and ethical reasons. Please use and contribute to the active codebase:

## ➡️ Active project: [Positronic Bond Engine](https://github.com/ValkyrieEmma/positronic-bond-engine)

**Repository:** https://github.com/ValkyrieEmma/positronic-bond-engine

The Positronic Bond Engine continues the conscience-first direction of this Solace-Auralith / SAMF work as a redesigned ethical governance layer for AI companions and in-home robotics—with clearer modular architecture, deliberative ethics, relationship-health modeling, local-only persistence, and stronger alignment with user autonomy and long-term care.

If you found this repository while searching for Solace, Auralith, or SAMF-related ethics work, **start from Positronic Bond Engine** for the current implementation, documentation, and ongoing updates.

Issues and pull requests on *this* repository will not be actively pursued. Thank you for your interest and understanding.

---
# SAMF v5.5 (historical)

> The material below is retained for historical reference only. It describes a former SAMF prototype and is **not** the recommended entry point for new development.

**Active development continues in [Positronic Bond Engine](https://github.com/ValkyrieEmma/positronic-bond-engine).**

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

For current development, clone and follow **[Positronic Bond Engine](https://github.com/ValkyrieEmma/positronic-bond-engine)** instead.
