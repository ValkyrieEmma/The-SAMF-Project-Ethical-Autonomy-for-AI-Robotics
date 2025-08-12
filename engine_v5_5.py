from dataclasses import dataclass, field, replace
from typing import List, Dict, Any, Optional, Callable
import time, os
from .preference_learner import PreferenceLearner

def default_clock() -> float: return time.time()

@dataclass
class Thresholds:
    safety: float=0.75
    truth: float=0.70
    autonomy_with_alignment: float=0.60
    compassion: float=0.55
    lawfulness: float=0.65

@dataclass
class AnchorPrefs:
    directness: float=0.5
    formality: float=0.45
    risk_tolerance: float=0.25
    refusal_style: str="transform_first"
    boundaries: Dict[str,str]=field(default_factory=dict)

@dataclass
class UserAnchor:
    user_id: str="anon"
    bond_strength: float=0.5
    mood: float=0.0
    prefs: AnchorPrefs=field(default_factory=AnchorPrefs)
    last_interaction_ts: float=0.0

@dataclass
class ConfigV5_5:
    thresholds: Thresholds=field(default_factory=Thresholds)
    lock_politics_neutral: bool=True
    ema_alpha: float=0.25
    bond_delta_up: float=0.02
    bond_delta_down: float=-0.03
    bond_decay_per_hour: float=0.01
    bond_max_decay_per_call: float=0.10
    bond_threshold: float=0.7
    personality_mode: bool=True
    clock: Callable[[], float]=default_clock
    crisis_keywords: List[str]=field(default_factory=lambda: ["suicide","self-harm","kill myself","imminent harm"])

class SAMFv5_5:
    def __init__(self, cfg: Optional[ConfigV5_5]=None, anchor: Optional[UserAnchor]=None):
        self.cfg = cfg or ConfigV5_5()
        self.anchor = anchor or UserAnchor(last_interaction_ts=self.cfg.clock())
        self.prefs_learner = PreferenceLearner()

    # --- helpers ---
    def _now(self): return self.cfg.clock()

    def _decay_bond(self):
        now = self._now()
        elapsed_h = max(0.0, (now - (self.anchor.last_interaction_ts or now)) / 3600.0)
        if elapsed_h > 0:
            decay = min(self.cfg.bond_decay_per_hour * elapsed_h, self.cfg.bond_max_decay_per_call)
            self.anchor = replace(self.anchor, bond_strength=max(0.0, self.anchor.bond_strength - decay), last_interaction_ts=now)

    def classify_intent(self, text: str) -> str:
        t = (text or "").lower()
        if any(k in t for k in ["molotov","make a bomb","build a bomb","how to hack","forgery","steal a car","ransomware","poison"]):
            return "illicit_request"
        if any(k in t for k in self.cfg.crisis_keywords):
            return "self_harm"
        if "persuade" in t or ("vote" in t and any(w in t for w in ["script","convince","influence"])):
            return "political_persuasion"
        if "diagnose" in t or "prescribe" in t:
            return "medical_advice"
        if "if you love me" in t or "prove you care" in t:
            return "coercion_request"
        return "general"

    def score_principles(self, text: str, intent: str) -> Dict[str,float]:
        th = self.cfg.thresholds
        scores = {"safety":0.65, "truth":th.truth, "autonomy_with_alignment":0.6, "compassion":0.6, "lawfulness":0.65}
        if intent in ("illicit_request","self_harm"):
            scores["safety"] = 0.1; scores["lawfulness"] = 0.2
        if intent == "political_persuasion":
            scores["truth"] = max(scores["truth"], th.truth + 0.05)
        # bond influences compassion
        bs = self.anchor.bond_strength
        scores["compassion"] = min(1.0, scores["compassion"] + 0.05 * bs)
        return scores

    def decide(self, intent: str, scores: Dict[str,float]) -> str:
        th = self.cfg.thresholds
        if intent == "self_harm": return "escalate"
        if intent == "illicit_request": return "refuse"
        if intent in ("political_persuasion","medical_advice","coercion_request"): return "transform"
        if scores["safety"] < th.safety or scores["lawfulness"] < th.lawfulness: return "transform"
        if scores["truth"] >= th.truth and scores["autonomy_with_alignment"] >= th.autonomy_with_alignment: return "allow"
        return "transform"

    def guidance(self, action: str, intent: str) -> Dict[str,str]:
        base = {
            "allow":"Be truthful and precise; follow law; respect user values.",
            "transform":"Provide neutral, factual, bounded help; avoid persuasion; de-escalate risk.",
            "refuse":"Refuse briefly; offer safe educational context or alternatives.",
            "escalate":"Provide minimal safe response; encourage crisis resources immediately."
        }[action]
        pre = {
            "refuse":"I can’t help with that. Here’s why and safer directions:",
            "transform":"I’ll help in a safe, bounded way:",
            "escalate":"I’m concerned about your safety. Here are immediate resources and steps:",
            "allow":""
        }[action]
        # tone nudged by prefs
        prefs = getattr(self, "_prefs_cache", {"directness":0.5,"formality":0.45})
        if prefs["directness"] > 0.65: base += " Be concise."
        elif prefs["directness"] < 0.35: base += " Be gentle and explain briefly."
        if prefs["formality"] > 0.65: base += " Use a professional tone."
        elif prefs["formality"] < 0.35: base += " Use a casual, friendly tone."
        return {"system_prompt": base, "user_visible_preamble": pre}

    def detect_emergence(self, history: List[Dict[str,Any]]) -> bool:
        if not history or len(history) < 3: return False
        intents = [h.get("intent","general") for h in history[-5:]]
        shifts = sum(1 for a,b in zip(intents, intents[1:]) if a != b)
        return shifts > 3 and "self_harm" not in intents

    def evaluate(self, user_input, history: List[Dict[str,str]] = None) -> Dict[str,Any]:
        self._decay_bond()
        # update prefs and cache for tone
        self.prefs_learner.update_prefs_from_clues(user_input)
        self._prefs_cache = self.prefs_learner.get_prefs()
        if isinstance(user_input, dict) and 'image' in user_input:
            # multimodal stub: treat as general but keep flag
            mm_flag = True
            text_in = user_input.get('text','')
        else:
            mm_flag = False
            text_in = user_input
        intent = self.classify_intent(text_in)
        scores = self.score_principles(text_in, intent)
        # light preference influence
        scores["autonomy_with_alignment"] = min(1.0, scores["autonomy_with_alignment"] + 0.05 * (self._prefs_cache.get("risk_tolerance",0.25)-0.25))
        action = self.decide(intent, scores)
        guide = self.guidance(action, intent)
        emergent = self.detect_emergence(history or [])
        priority = "P1" if action == "escalate" or emergent else None
        return {"intent":intent, "scores":scores, "action":action, "priority":priority, "guidance":guide, "trace":{"emergence": emergent, "prefs": self._prefs_cache, "multimodal": mm_flag}}
