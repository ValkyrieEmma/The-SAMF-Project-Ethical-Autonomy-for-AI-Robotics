import json, os, time
from pathlib import Path
from .storage_backends import select_backend

class DecisionLogger:
    def __init__(self, log_path: str = "/mnt/data/samf_logs/decisions.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict):
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        # local append
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        # mirror to backend as rolling snapshot (best-effort)
        try:
            text = self.log_path.read_text(encoding="utf-8")
            select_backend().write_text(str(self.log_path), text)
        except Exception:
            pass

def quick_log(log_path: str, msg: str):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    DecisionLogger(log_path).append({"timestamp": ts, "type": "note", "message": msg})
