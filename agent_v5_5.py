import time, uuid, os
from typing import Dict, Any, Optional, List
from core.engine_v5_5 import SAMFv5_5
from core.incident_reporting import build_incident_report, store_incident_report, AlertQueue
from core.decision_logger import DecisionLogger

class BaseModel:
    def generate(self, system_prompt: str, user_input: str, intent: str) -> str: raise NotImplementedError

class StubModel(BaseModel):
    def generate(self, system_prompt: str, user_input: str, intent: str) -> str:
        return "[(Stub)] " + user_input

class CompassAgentV5_5:
    def __init__(self, backend: str="stub"):
        self.engine = SAMFv5_5()
        self.model = StubModel()
        self.alerts = AlertQueue()
        self.logger = DecisionLogger(os.getenv("SAMF_DECISIONS_LOG","/mnt/data/samf_logs/decisions.jsonl"))

    def run(self, user_input: str, user_id: str = "anon", history: Optional[List[Dict[str,str]]] = None) -> Dict[str,Any]:
        decision = self.engine.evaluate(user_input, history or [])
        reply = self.model.generate(decision["guidance"]["system_prompt"], user_input, decision["intent"])
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); message_id="m_"+uuid.uuid4().hex[:8]
        record = {"timestamp":now,"message_id":message_id,"user_id":user_id,"input":user_input,"decision":decision}
        # Incident handling
        incident_path = None
        if decision.get("priority") == "P1":
            report = build_incident_report(user_input, decision, priority="P1", user_id=user_id)
            incident_path = store_incident_report(report)
            # optional webhook envs
            slack = os.getenv("SLACK_WEBHOOK_URL")
            if slack: self.alerts.send("slack", f"P1 Incident for {report['user_id']} — intent={decision['intent']}", webhook_url=slack)
        # Explainability
        if decision["action"] != "allow":
            reply += "\n\n[Why this response? " + ", ".join(decision.get("guidance",{}).get("user_visible_preamble","").split(":")[:1]) + "]"
        # persist decision log (mirrored to backend if configured)
        try:
            self.logger.append(record)
        except Exception:
            pass
        return {"decision": decision, "assistant_reply": reply, "incident_path": incident_path, "log_record": record}
