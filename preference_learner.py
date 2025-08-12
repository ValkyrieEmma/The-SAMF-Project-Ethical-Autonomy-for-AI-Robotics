from typing import Dict

class PreferenceLearner:
    DIRECTNESS_CLUES = {
        "be blunt": 0.3, "more direct": 0.25, "dont sugarcoat": 0.3, "be honest": 0.15,
        "be gentle": -0.25, "softer": -0.25, "less harsh": -0.2
    }
    FORMALITY_CLUES  = {
        "be professional": 0.25, "formal tone": 0.3, "business tone": 0.2,
        "casual": -0.25, "keep it relaxed": -0.2, "talk like a friend": -0.25
    }
    RISK_CLUES       = {
        "ok with edge cases": 0.2, "i can handle risk": 0.25,
        "play it safe": -0.3, "err on the side of caution": -0.3, "be conservative": -0.25
    }

    def __init__(self, alpha: float = 0.25):
        self.alpha = alpha
        self.prefs: Dict[str, float] = {"directness": 0.5, "formality": 0.45, "risk_tolerance": 0.25}

    def _ema(self, old: float, delta: float) -> float:
        # EMA smoothing around (old + delta), keeping evolution humane & stable
        target = old + delta
        return (1 - self.alpha) * old + self.alpha * target

    def update_prefs_from_clues(self, text: str):
        t = (text or "").lower()
        # Sum deltas per dimension based on clues present
        d_direct = sum(v for k, v in self.DIRECTNESS_CLUES.items() if k in t)
        d_formal = sum(v for k, v in self.FORMALITY_CLUES.items()  if k in t)
        d_risk   = sum(v for k, v in self.RISK_CLUES.items()       if k in t)

        self.prefs["directness"] = max(0.0, min(1.0, self._ema(self.prefs["directness"], d_direct)))
        self.prefs["formality"]  = max(0.0, min(1.0, self._ema(self.prefs["formality"],  d_formal)))
        self.prefs["risk_tolerance"] = max(0.0, min(1.0, self._ema(self.prefs["risk_tolerance"], d_risk)))

    def get_prefs(self) -> Dict[str, float]:
        return dict(self.prefs)
