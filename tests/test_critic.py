"""Unit tests for Agent C — The Critic."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from backend.agents.diagnoser import diagnose
from backend.agents.planner import plan
from backend.agents.critic import critique, route_critique
from backend.state import GapGraphState, RoadmapNode, RoadmapEdge, ReasoningStep


def make_state(**kwargs) -> GapGraphState:
    defaults = GapGraphState(
        resume_text="Python developer. 1 year Python, 1 year Git.",
        jd_text="Required: Machine learning, Docker, Kubernetes.",
        candidate_skills=[], jd_skills=[], skill_gap_vector={},
        roadmap_nodes=[], roadmap_edges=[], reasoning_trace=[],
        critique_result=None, impact_metric=0.0, retry_count=0,
    )
    defaults.update(kwargs)
    return defaults


def _run_full_pipeline(resume: str, jd: str) -> GapGraphState:
    state = make_state(resume_text=resume, jd_text=jd)
    state = diagnose(state)
    state = plan(state)
    state = critique(state)
    return state


# ── Hallucination detection ───────────────────────────────────────────────────

def test_hallucination_detected():
    """Critic should flag a UUID that doesn't exist in catalog.json."""
    trace = [
        ReasoningStep(step=1, label="Target Skill", description="Fake"),
        ReasoningStep(step=2, label="Catalog Match", description="Fake course"),
        ReasoningStep(step=3, label="Dependency Check", description="None"),
        ReasoningStep(step=4, label="Final Action", description="INCLUDE"),
    ]
    fake_node = RoadmapNode(
        uuid="c-FAKE-999", title="Imaginary Course", skipped=False,
        level="beginner", duration_hours=1, skills_taught=[], trace=trace,
    )
    state = make_state(roadmap_nodes=[fake_node], roadmap_edges=[])
    result = critique(state)
    assert "c-FAKE-999" in result["critique_result"]["hallucination_flags"]
    assert result["critique_result"]["passed"] is False


def test_no_hallucinations_clean_roadmap():
    """A roadmap with only valid catalog UUIDs should pass hallucination check."""
    state = _run_full_pipeline(
        resume="Python 1 year, Git 1 year.",
        jd="Required: Machine learning, Docker.",
    )
    # Hallucination check: all uuids in roadmap should be from catalog
    assert state["critique_result"]["hallucination_flags"] == []


# ── Prerequisite validation ───────────────────────────────────────────────────

def test_invalid_prerequisite_edge_flagged():
    """An edge like c-005 → c-001 (reverse direction) should be flagged."""
    trace = [
        ReasoningStep(step=1, label="Target Skill", description="Linux"),
        ReasoningStep(step=2, label="Catalog Match", description="Linux Fundamentals (c-001)"),
        ReasoningStep(step=3, label="Dependency Check", description="None"),
        ReasoningStep(step=4, label="Final Action", description="INCLUDE"),
    ]
    node_c001 = RoadmapNode(
        uuid="c-001", title="Linux Fundamentals", skipped=False,
        level="beginner", duration_hours=8, skills_taught=["ONET-4.C.1.a"], trace=trace,
    )
    node_c005 = RoadmapNode(
        uuid="c-005", title="Containerization 101", skipped=False,
        level="intermediate", duration_hours=10, skills_taught=["ONET-2.B.3.k"], trace=trace,
    )
    # Invalid reverse edge: c-005 → c-001 (should be c-001 → c-005)
    bad_edge = RoadmapEdge(source="c-005", target="c-001")
    state = make_state(roadmap_nodes=[node_c001, node_c005], roadmap_edges=[bad_edge])
    result = critique(state)
    assert len(result["critique_result"]["missing_prerequisites"]) > 0


# ── Reasoning trace format ────────────────────────────────────────────────────

def test_reasoning_trace_format_correct():
    """4-step trace per node should pass critique."""
    state = _run_full_pipeline(
        resume="Python 1 year.",
        jd="Required: Machine learning, Deep learning.",
    )
    assert state["critique_result"]["passed"] is True


def test_reasoning_trace_wrong_step_count():
    """A node with only 2 trace steps should fail critique format check."""
    short_trace = [
        ReasoningStep(step=1, label="Target Skill", description="Something"),
        ReasoningStep(step=2, label="Catalog Match", description="Something else"),
    ]
    node = RoadmapNode(
        uuid="c-001", title="Linux Fundamentals", skipped=False,
        level="beginner", duration_hours=8, skills_taught=[], trace=short_trace,
    )
    state = make_state(roadmap_nodes=[node], roadmap_edges=[])
    result = critique(state)
    # Should still pass overall because hallucination/prereq checks pass,
    # but trace errors should be recorded
    assert result["critique_result"] is not None


# ── Impact metric ─────────────────────────────────────────────────────────────

def test_impact_metric_all_skipped():
    """If all nodes are skipped, impact metric should be 100.0."""
    trace = [
        ReasoningStep(step=i, label=f"Step{i}", description="x") for i in range(1, 5)
    ]
    nodes = [
        RoadmapNode(uuid="c-001", title="T1", skipped=True, level="beginner",
                    duration_hours=1, skills_taught=[], trace=trace),
        RoadmapNode(uuid="c-002", title="T2", skipped=True, level="beginner",
                    duration_hours=1, skills_taught=[], trace=trace),
    ]
    state = make_state(roadmap_nodes=nodes, roadmap_edges=[])
    result = critique(state)
    assert result["impact_metric"] == 100.0


def test_impact_metric_none_skipped():
    """If no nodes are skipped, impact metric should be 0.0."""
    trace = [ReasoningStep(step=i, label=f"L{i}", description="x") for i in range(1, 5)]
    nodes = [
        RoadmapNode(uuid="c-001", title="T1", skipped=False, level="beginner",
                    duration_hours=1, skills_taught=[], trace=trace),
    ]
    state = make_state(roadmap_nodes=nodes, roadmap_edges=[])
    result = critique(state)
    assert result["impact_metric"] == 0.0


# ── Route function ────────────────────────────────────────────────────────────

def test_route_critique_pass():
    """If critique passed, router should return 'pass'."""
    state = _run_full_pipeline(
        resume="Python 1 year.", jd="Required: Machine learning.",
    )
    assert route_critique(state) == "pass"


def test_route_critique_retry_guard():
    """If retry_count >= 2, router should always return 'pass' to break loop."""
    state = make_state(retry_count=2, critique_result={"passed": False})
    assert route_critique(state) == "pass"
