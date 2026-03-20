"""
End-to-End Integration Test
Calls POST /analyze with sample resume + JD fixtures via httpx.AsyncClient.
Validates the full response schema and DAG acyclicity.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import networkx as nx
import httpx
from pathlib import Path

# Check if OpenAI key is set — e2e with LLM requires it
OPENAI_KEY_SET = bool(os.getenv("OPENAI_API_KEY", "").strip() and
                      os.getenv("OPENAI_API_KEY") != "sk-...")

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_analyze_endpoint_full_pipeline():
    """Full pipeline test via /analyze endpoint using real FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    resume_path = FIXTURES_DIR / "resume.txt"
    jd_path = FIXTURES_DIR / "jd.txt"

    with open(resume_path, "rb") as f_resume:
        jd_text = jd_path.read_text()
        response = client.post(
            "/analyze",
            files={"resume": ("resume.txt", f_resume, "text/plain")},
            data={"jd": jd_text},
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()

    # Required top-level fields
    assert "skill_gap_vector" in data, "Missing skill_gap_vector"
    assert "roadmap" in data, "Missing roadmap"
    assert "reasoning_trace" in data, "Missing reasoning_trace"
    assert "impact_metric" in data, "Missing impact_metric"

    # Skill-gap vector structure
    for skill_name, info in data["skill_gap_vector"].items():
        assert "candidate" in info
        assert "required" in info
        assert "gap" in info

    # Roadmap structure
    roadmap = data["roadmap"]
    assert "nodes" in roadmap
    assert "edges" in roadmap
    assert len(roadmap["nodes"]) > 0, "Roadmap should have at least one node"

    # Impact metric range
    assert 0.0 <= data["impact_metric"] <= 100.0

    # Roadmap DAG acyclicity
    G = nx.DiGraph()
    for node in roadmap["nodes"]:
        G.add_node(node["uuid"])
    for edge in roadmap["edges"]:
        G.add_edge(edge["source"], edge["target"])
    assert nx.is_directed_acyclic_graph(G), "Roadmap must be a DAG — cycles detected!"


def test_health_endpoint():
    """Health check should return 200."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    """Root should return API info."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data


def test_diagnose_debug_endpoint():
    """Debug /diagnose endpoint should return candidate_skills and jd_skills."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resume_path = FIXTURES_DIR / "resume.txt"
    jd_path = FIXTURES_DIR / "jd.txt"

    with open(resume_path, "rb") as f_resume:
        response = client.post(
            "/diagnose",
            files={"resume": ("resume.txt", f_resume, "text/plain")},
            data={"jd": jd_path.read_text()},
        )

    assert response.status_code == 200
    data = response.json()
    assert "candidate_skills" in data
    assert "jd_skills" in data
    assert "skill_gap_vector" in data


def test_plan_debug_endpoint():
    """Debug /plan endpoint should return a roadmap."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resume_path = FIXTURES_DIR / "resume.txt"
    jd_path = FIXTURES_DIR / "jd.txt"

    with open(resume_path, "rb") as f_resume:
        response = client.post(
            "/plan",
            files={"resume": ("resume.txt", f_resume, "text/plain")},
            data={"jd": jd_path.read_text()},
        )

    assert response.status_code == 200
    data = response.json()
    assert "roadmap" in data


def test_bad_request_empty_jd():
    """Empty JD should return 400."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resume_path = FIXTURES_DIR / "resume.txt"

    with open(resume_path, "rb") as f_resume:
        response = client.post(
            "/analyze",
            files={"resume": ("resume.txt", f_resume, "text/plain")},
            data={"jd": "   "},
        )

    assert response.status_code == 400
