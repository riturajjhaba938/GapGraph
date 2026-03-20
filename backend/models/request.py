"""
API Request and Response Pydantic models.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.skill import NormalizedSkillModel, SkillGapEntry
from backend.models.roadmap import RoadmapModel, ReasoningStepModel
from backend.models.critique import CritiqueReportModel


class AnalyzeRequest(BaseModel):
    """
    Request model for the main /analyze endpoint.
    (Note: Since /analyze uses multipart/form-data for the PDF upload,
    this model is primarily for documentation and testing.)
    """
    jd_text: str = Field(..., description="The raw job description text.")


class AnalyzeResponse(BaseModel):
    """
    Full response from the /analyze endpoint.
    """
    skill_gap_vector: Dict[str, SkillGapEntry] = Field(
        ...,
        description="Dictionary mapping skill names to their gap analysis.",
    )
    roadmap: RoadmapModel = Field(..., description="The generated training DAG.")
    reasoning_trace: List[ReasoningStepModel] = Field(
        ...,
        description="Combined reasoning steps for all courses in the roadmap.",
    )
    impact_metric: float = Field(
        ...,
        description="Percentage of the standard curriculum bypassed (0-100).",
        example=37.5,
    )
    critique: Optional[CritiqueReportModel] = Field(
        None,
        description="The final validation report from Agent C.",
    )


class DiagnoseResponse(BaseModel):
    """Response from the /diagnose debug endpoint."""
    candidate_skills: List[NormalizedSkillModel]
    jd_skills: List[NormalizedSkillModel]
    skill_gap_vector: Dict[str, SkillGapEntry]


class PlanResponse(BaseModel):
    """Response from the /plan debug endpoint."""
    roadmap: RoadmapModel
    reasoning_trace: List[ReasoningStepModel]


class CritiqueResponse(BaseModel):
    """Response from the /critique debug endpoint."""
    critique_result: CritiqueReportModel
    impact_metric: float
