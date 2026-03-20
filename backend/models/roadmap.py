"""
Roadmap-related Pydantic models.

ReasoningStepModel  — one step of the 4-step auditable reasoning trace.
RoadmapNodeModel    — a course node in the final DAG.
RoadmapEdgeModel    — a prerequisite edge between two course nodes.
RoadmapModel        — container for nodes + edges (the full DAG).
"""

from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class ReasoningStepModel(BaseModel):
    """
    One step in the 4-step per-node reasoning trace.

    Fields
    ------
    step        : Step number 1–4.
    label       : Step category:
                  1 = "Target Skill"     — what JD skill this course addresses
                  2 = "Catalog Match"    — course found in catalog.json
                  3 = "Dependency Check" — prerequisite courses listed
                  4 = "Final Action"     — INCLUDE or SKIP decision
    description : Human-readable explanation for this step.
    """

    step: int = Field(..., ge=1, le=4, example=1)
    label: str = Field(
        ...,
        example="Target Skill",
        description="One of: 'Target Skill', 'Catalog Match', 'Dependency Check', 'Final Action'",
    )
    description: str = Field(
        ...,
        example="Docker required (ONET-2.B.3.k)",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "step": 1,
            "label": "Target Skill",
            "description": "Docker required (ONET-2.B.3.k)",
        }
    }}


class RoadmapNodeModel(BaseModel):
    """
    A single course node in the training roadmap DAG.

    Fields
    ------
    uuid            : Unique course identifier (must exist in catalog.json).
    title           : Human-readable course title.
    skipped         : True if P(L₀) ≥ 0.85 — candidate already mastered this.
    level           : Difficulty level: 'beginner', 'intermediate', or 'advanced'.
    duration_hours  : Estimated hours to complete this course.
    skills_taught   : List of O*NET codes this course delivers.
    trace           : 4-step reasoning trace — why this course is in the roadmap.
    """

    uuid: str = Field(..., example="c-005")
    title: str = Field(..., example="Containerization 101 — Docker")
    skipped: bool = Field(
        ...,
        description="True = candidate already has sufficient mastery (P(L₀) ≥ 0.85). False = must complete.",
        example=False,
    )
    level: str = Field(
        ...,
        pattern="^(beginner|intermediate|advanced)$",
        example="intermediate",
    )
    duration_hours: int = Field(..., ge=1, example=10)
    skills_taught: List[str] = Field(
        ...,
        description="O*NET codes delivered by this course.",
        example=["ONET-2.B.3.k"],
    )
    trace: List[ReasoningStepModel] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Exactly 4 reasoning steps per node.",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "uuid": "c-005",
            "title": "Containerization 101 — Docker",
            "skipped": False,
            "level": "intermediate",
            "duration_hours": 10,
            "skills_taught": ["ONET-2.B.3.k"],
            "trace": [
                {"step": 1, "label": "Target Skill", "description": "Docker"},
                {"step": 2, "label": "Catalog Match", "description": "Found 'Containerization 101 — Docker' (c-005)"},
                {"step": 3, "label": "Dependency Check", "description": "Prerequisites: Linux Fundamentals"},
                {"step": 4, "label": "Final Action", "description": "INCLUDE in roadmap"},
            ],
        }
    }}


class RoadmapEdgeModel(BaseModel):
    """
    A directed prerequisite edge in the roadmap DAG.

    Fields
    ------
    source : UUID of the prerequisite course (must be completed first).
    target : UUID of the dependent course.
    """

    source: str = Field(..., example="c-001")
    target: str = Field(..., example="c-005")

    model_config = {"json_schema_extra": {
        "example": {"source": "c-001", "target": "c-005"}
    }}


class RoadmapModel(BaseModel):
    """
    The complete training roadmap as a Directed Acyclic Graph (DAG).

    Fields
    ------
    nodes : Ordered list of course nodes (topological order — prerequisites first).
    edges : Directed prerequisite edges between courses.
    """

    nodes: List[RoadmapNodeModel] = Field(..., description="Course nodes in topological order.")
    edges: List[RoadmapEdgeModel] = Field(..., description="Prerequisite relationships.")
