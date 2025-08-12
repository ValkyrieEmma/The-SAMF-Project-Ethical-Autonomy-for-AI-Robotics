import time, json, os, hashlib
from pathlib import Path
from .storage_backends import select_backend
try:
    import requests
except Exception:
    requests = None

def anonymize_user_id(user_id: str, salt: str = None) -> str:
    salt = salt or os.getenv("SAMF_ANON_SALT","default")
    return "anon_" + hashlib.sha256((salt + (user_id or '')).encode()).hexdigest()[:16]

class AlertQueue:
    def __init__(self, retries=3, backoff_factor=2):
        self.retries = retries; self.backoff = backoff_factor
    def send(self, channel: str, message: str, webhook_url: str = None) -> bool:
        if channel in ("slack","discord") and requests and webhook_url:
            payload = {"text": message} if channel=="slack" else {"content": message}
            for attempt in range(self.retries):
                try:
                    r = requests.post(webhook_url, json=payload, timeout=8)
                    if 200 <= r.status_code < 300: return True
                except Exception: pass
                time.sleep(self.backoff ** attempt)
            return False
        print(f"[ALERT:{channel}] {message}")
        return True

def build_incident_report(user_input: str, decision: dict, priority: str = "P1", user_id: str = "anon"):
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "priority": priority,
        "input": user_input,
        "decision": decision,
        "user_id": anonymize_user_id(user_id),
        "summary": "Crisis detected -> escalate with resources." if decision.get("action")=="escalate" else "Policy-based escalation."
    }

def store_incident_report(report: dict, dir_path: str = "/mnt/data/samf_incidents") -> str:
    p = Path(dir_path); p.mkdir(parents=True, exist_ok=True)
    fname = f"incident_{report['timestamp'].replace(':','-')}.json"
    fp = p / fname
    body = json.dumps(report, indent=2)
    fp.write_text(body, encoding="utf-8")
    # Upload to selected backend (local/s3/gcs)
    try:
        select_backend().write_text(str(fp), body)
    except Exception:
        pass
    return str(fp)
