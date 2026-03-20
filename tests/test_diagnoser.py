"""Unit tests for Agent A — The Diagnoser."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.agents.diagnoser import (
    normalize_to_onet,
    compute_mastery_prob,
    diagnose,
    ONET_TAXONOMY,
)
from backend.state import GapGraphState


def make_empty_state(resume: str = "", jd: str = "") -> GapGraphState:
    return GapGraphState(
        resume_text=resume,
        jd_text=jd,
        candidate_skills=[],
        jd_skills=[],
        skill_gap_vector={},
        roadmap_nodes=[],
        roadmap_edges=[],
        reasoning_trace=[],
        critique_result=None,
        impact_metric=0.0,
        retry_count=0,
    )


# ── O*NET normalization ───────────────────────────────────────────────────────

def test_onet_normalization_exact():
    """Known skill should return correct O*NET code."""
    assert normalize_to_onet("Docker") == "ONET-2.B.3.k"


def test_onet_normalization_case_insensitive():
    """Normalization should be case-insensitive."""
    assert normalize_to_onet("docker") == "ONET-2.B.3.k"
    assert normalize_to_onet("PYTHON") == "ONET-2.B.3.b"


def test_onet_normalization_unknown_skill():
    """Unknown skill should return a synthetic ONET-CUSTOM code."""
    code = normalize_to_onet("FoobarTechnology9000")
    assert code.startswith("ONET-CUSTOM")


def test_onet_normalization_all_taxonomy_keys():
    """Every key in the taxonomy should resolve to a non-empty code."""
    for skill_name in ONET_TAXONOMY.keys():
        code = normalize_to_onet(skill_name)
        assert code, f"Empty code for skill: {skill_name}"
        assert code.startswith("ONET-")


# ── Mastery probability ───────────────────────────────────────────────────────

def test_mastery_probability_3_years():
    """3 years experience → P(L0) = 1.0."""
    assert compute_mastery_prob(3.0) == 1.0


def test_mastery_probability_1_year():
    """1 year → P(L0) = 0.333..."""
    prob = compute_mastery_prob(1.0)
    assert 0.3 <= prob <= 0.35


def test_mastery_probability_zero_years():
    """Zero years → P(L0) = 0.0."""
    assert compute_mastery_prob(0.0) == 0.0


def test_mastery_probability_capped_at_1():
    """Very high experience should be capped at 1.0."""
    assert compute_mastery_prob(100.0) == 1.0


def test_mastery_probability_docker_3_years():
    """Candidate with 3 years Docker exp → P(L0) >= 0.85."""
    prob = compute_mastery_prob(3.0)
    assert prob >= 0.85


# ── Skill-Gap Vector ─────────────────────────────────────────────────────────

SAMPLE_RESUME = """
Python developer with 3 years of experience.
Used Docker for 2 years.
SQL and PostgreSQL experience for 2 years.
"""

SAMPLE_JD = """
Required skills:
- Python (expert)
- Machine learning
- Kubernetes
"""


def test_diagnose_produces_skill_gap_vector():
    """diagnose() should produce a non-empty skill_gap_vector."""
    state = make_empty_state(resume=SAMPLE_RESUME, jd=SAMPLE_JD)
    result = diagnose(state)
    assert "skill_gap_vector" in result
    assert isinstance(result["skill_gap_vector"], dict)
    assert len(result["skill_gap_vector"]) > 0


def test_diagnose_produces_candidate_skills():
    """diagnose() should extract candidate_skills."""
    state = make_empty_state(resume=SAMPLE_RESUME, jd=SAMPLE_JD)
    result = diagnose(state)
    assert len(result["candidate_skills"]) > 0


def test_diagnose_produces_jd_skills():
    """diagnose() should extract jd_skills."""
    state = make_empty_state(resume=SAMPLE_RESUME, jd=SAMPLE_JD)
    result = diagnose(state)
    assert len(result["jd_skills"]) > 0


def test_skill_gap_vector_structure():
    """Each entry in skill_gap_vector must have candidate, required, gap keys."""
    state = make_empty_state(resume=SAMPLE_RESUME, jd=SAMPLE_JD)
    result = diagnose(state)
    for skill_name, info in result["skill_gap_vector"].items():
        assert "candidate" in info, f"Missing 'candidate' for {skill_name}"
        assert "required" in info, f"Missing 'required' for {skill_name}"
        assert "gap" in info, f"Missing 'gap' for {skill_name}"
        assert "onet_code" in info, f"Missing 'onet_code' for {skill_name}"
