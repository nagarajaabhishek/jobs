from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class JobEvaluationSchema(BaseModel):
    location_verification: str = Field(..., description="Confirmed: USA/Dubai/Remote or Invalid")
    h1b_sponsorship: str = Field(..., description="Likely, Unlikely, or Unknown")
    recommended_resume: str = Field(..., description="The specific resume role name")
    reasoning: str = Field(..., description="Deep analysis of fit based on skills and resume")
    salary_range: str = Field(default="Not mentioned")
    tech_stack: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    apply_conviction_score: int = Field(..., ge=0, le=100)
    verdict: str = Field(..., description="Auto-Apply, Strong Match, Worth Considering, or No")
    # Evidence & auditability (required for non-hallucinated reuse in resume building/upskilling)
    score_breakdown: Dict[str, int] = Field(default_factory=dict, description="Named components that sum to apply_conviction_score")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="List of evidence items with jd_quote and profile_evidence")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    jd_quality: str = Field(default="unknown", description="high|medium|low|unknown")
    output_quality: str = Field(default="unknown", description="high|medium|low|unknown")

    model_config = {
        "json_schema_extra": {
            "example": {
                "location_verification": "Confirmed: USA",
                "h1b_sponsorship": "Likely",
                "recommended_resume": "Product Manager (TPM)",
                "reasoning": "User has 5+ years of Python/SQL experience which matches the JD perfectly.",
                "salary_range": "$120k-$150k",
                "tech_stack": ["Python", "SQL", "AWS"],
                "skill_gaps": ["React", "Go"],
                "apply_conviction_score": 85,
                "verdict": "Auto-Apply",
                "score_breakdown": {"skill_match": 40, "role_fit": 15, "strategic_priority": 15, "sponsorship": 5, "experience_gap": 10},
                "evidence": [{"jd_quote": "SQL required", "profile_evidence": "DenseMatrix: core skills include SQL", "type": "match"}],
                "confidence": 0.8,
                "jd_quality": "high",
                "output_quality": "high",
            }
        }
    }
