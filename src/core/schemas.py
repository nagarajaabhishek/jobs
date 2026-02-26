from pydantic import BaseModel, Field
from typing import List, Optional

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
                "verdict": "Auto-Apply"
            }
        }
    }
