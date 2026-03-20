"""
Critique report Pydantic model — returned by Agent C (The Critic).
"""

from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class CritiqueReportModel(BaseModel):
    """
    Validation report produced by Agent C after checking the roadmap.

    Fields
    ------
    passed                : True if all checks passed — roadmap is safe to use.
    hallucination_flags   : List of course UUIDs in the roadmap that do NOT exist
                            in catalog.json. Empty list = no hallucinations.
    missing_prerequisites : List of edge violations where a prerequisite relationship
                            is invalid or missing from the catalog.
    message               : Human-readable summary of the critique result.
    """

    passed: bool = Field(
        ...,
        description="True = roadmap passed all validation checks.",
        example=True,
    )
    hallucination_flags: List[str] = Field(
        default_factory=list,
        description="UUIDs of courses not found in catalog.json.",
        example=[],
    )
    missing_prerequisites: List[str] = Field(
        default_factory=list,
        description="Descriptions of invalid prerequisite edges.",
        example=[],
    )
    message: str = Field(
        ...,
        example="Roadmap validated successfully. 8 courses (3 skipped). Impact metric: 37.5% curriculum bypassed.",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "passed": True,
            "hallucination_flags": [],
            "missing_prerequisites": [],
            "message": "Roadmap validated successfully. 8 courses (3 skipped). Impact metric: 37.5% curriculum bypassed.",
        }
    }}
