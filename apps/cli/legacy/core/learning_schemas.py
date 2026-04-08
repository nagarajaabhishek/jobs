"""Schemas for feedback learning, score calibration, and decision audit (full-cycle adoption)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DecisionAudit:
    """Machine-readable score decomposition for a single job evaluation."""

    base_llm_score: int
    calibration_delta: int
    final_score: int
    matched_patterns: List[Dict[str, Any]] = field(default_factory=list)
    cycle_id: str = ""
    notes: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "DecisionAudit":
        if not s or not str(s).strip():
            return cls(base_llm_score=0, calibration_delta=0, final_score=0)
        try:
            d = json.loads(s)
            return cls(
                base_llm_score=int(d.get("base_llm_score", 0)),
                calibration_delta=int(d.get("calibration_delta", 0)),
                final_score=int(d.get("final_score", 0)),
                matched_patterns=list(d.get("matched_patterns") or []),
                cycle_id=str(d.get("cycle_id") or ""),
                notes=str(d.get("notes") or ""),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls(base_llm_score=0, calibration_delta=0, final_score=0)


@dataclass
class LearnedPattern:
    """A single boost/penalize pattern learned from user feedback."""

    pattern_type: str  # "boost" | "penalize"
    pattern_value: str  # normalized phrase or token
    weight_adjustment: float  # applied as integer delta after scaling
    confidence: float = 0.5
    learned_from_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LearnedPattern":
        return cls(
            pattern_type=str(d.get("pattern_type", "boost")),
            pattern_value=str(d.get("pattern_value", "")),
            weight_adjustment=float(d.get("weight_adjustment", 0.0)),
            confidence=float(d.get("confidence", 0.5)),
            learned_from_count=int(d.get("learned_from_count", 0)),
        )


@dataclass
class FeedbackEvent:
    """One user feedback record (ingested from sheet or CLI)."""

    job_url_canonical: str
    feedback_type: str  # thumbs_up | thumbs_down | note
    feedback_text: str
    created_at: str
    row_hint: Optional[str] = None  # optional sheet row context

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# Column names used in Google Sheets (must match GoogleSheetsClient)
SHEET_COL_FEEDBACK = "Feedback"
SHEET_COL_FEEDBACK_NOTE = "Feedback Note"
SHEET_COL_CALIBRATION_DELTA = "Calibration Delta"
SHEET_COL_DECISION_AUDIT = "Decision Audit JSON"
SHEET_COL_DIGEST_STATUS = "Digest Status"
SHEET_COL_ACTION_LINK = "Action Link"
SHEET_COL_BASE_LLM_SCORE = "Base LLM Score"
SHEET_COL_EVIDENCE_JSON = "Evidence JSON"
SHEET_COL_JD_VERIFIED = "JD Verified"
SHEET_COL_JD_FETCH_METHOD = "JD Fetch Method"
SHEET_COL_JD_FETCH_REASON = "JD Fetch Reason"
