"""
GapGraph Shared State Schema
LangGraph TypedDict passed between all agents.
"""

from __future__ import annotations

from typing import TypedDict, List, Optional, Dict, Any


class NormalizedSkill(TypedDict):
    """A skill extracted from resume or JD, normalized to O*NET code."""
    name: str                   # Raw skill name (e.g. "Docker")
    onet_code: str              # e.g. "ONET-2.B.3.k"
    years_experience: float     # candidate only; 0.0 for JD
    required_level: float       # JD only (0-1); 0.0 for candidate
    mastery_prob: float         # P(L0): initial mastery probability (0-1)


class ReasoningStep(TypedDict):
    """One step of the 4-step reasoning trace per roadmap node."""
    step: int                   # 1-4
    label: str                  # e.g. "Target Skill"
    description: str            # e.g. "Docker required (ONET-2.B.3.k)"


class RoadmapNode(TypedDict):
    uuid: str
    title: str
    skipped: bool
    level: str
    duration_hours: int
    skills_taught: List[str]
    trace: List[ReasoningStep]


class RoadmapEdge(TypedDict):
    source: str                 # uuid of prerequisite course
    target: str                 # uuid of dependent course


class CritiqueReport(TypedDict):
    passed: bool
    hallucination_flags: List[str]   # uuids not in catalog
    missing_prerequisites: List[str] # edge violations
    message: str


class GapGraphState(TypedDict):
    """Full pipeline state shared across all LangGraph nodes."""
    resume_text: str
    jd_text: str
    candidate_skills: List[NormalizedSkill]
    jd_skills: List[NormalizedSkill]
    skill_gap_vector: Dict[str, Dict[str, float]]   # {skill: {candidate, required, gap}}
    roadmap_nodes: List[RoadmapNode]
    roadmap_edges: List[RoadmapEdge]
    reasoning_trace: List[ReasoningStep]
    critique_result: Optional[CritiqueReport]
    impact_metric: float                             # % curriculum skipped
    retry_count: int                                 # guard against infinite loops
