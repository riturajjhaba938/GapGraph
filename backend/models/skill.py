"""
Skill-related Pydantic models.

NormalizedSkillModel  — one skill extracted from resume or JD, mapped to O*NET.
SkillGapEntry         — one row in the Skill-Gap Vector response.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class NormalizedSkillModel(BaseModel):
    """
    A single skill extracted from a resume or JD and normalized to an O*NET code.

    Fields
    ------
    name              : Raw skill name as extracted (e.g. "Docker").
    onet_code         : O*NET SOC code (e.g. "ONET-2.B.3.k").
    years_experience  : How many years the candidate has used this skill.
                        Always 0.0 for JD skills.
    required_level    : Target proficiency 0.0–1.0 required by the JD.
                        Always 0.0 for candidate skills.
    mastery_prob      : P(L₀) — initial mastery probability (0.0–1.0).
                        Computed as min(1.0, years/3 × frequency_score).
                        Always 0.0 for JD skills.
    """

    name: str = Field(..., example="Docker")
    onet_code: str = Field(..., example="ONET-2.B.3.k")
    years_experience: float = Field(0.0, ge=0.0, example=2.0)
    required_level: float = Field(0.0, ge=0.0, le=1.0, example=0.8)
    mastery_prob: float = Field(0.0, ge=0.0, le=1.0, example=0.667)

    model_config = {"json_schema_extra": {
        "example": {
            "name": "Docker",
            "onet_code": "ONET-2.B.3.k",
            "years_experience": 2.0,
            "required_level": 0.0,
            "mastery_prob": 0.667,
        }
    }}


class SkillGapEntry(BaseModel):
    """
    One entry in the Skill-Gap Vector.
    Compares the candidate's proficiency against the JD requirement for a single skill.

    Fields
    ------
    onet_code  : Normalized O*NET code for this skill.
    candidate  : Candidate's estimated mastery (0.0–1.0).
    required   : JD-required proficiency level (0.0–1.0).
    gap        : required − candidate. Positive = needs training. Negative = exceeds requirement.
    """

    onet_code: str = Field(..., example="ONET-2.B.3.k")
    candidate: float = Field(..., ge=0.0, le=1.0, example=0.667)
    required: float = Field(..., ge=0.0, le=1.0, example=0.8)
    gap: float = Field(..., example=0.133)

    model_config = {"json_schema_extra": {
        "example": {
            "onet_code": "ONET-2.B.3.k",
            "candidate": 0.667,
            "required": 0.8,
            "gap": 0.133,
        }
    }}
