"""
API Router for /analyze and individual agent debug endpoints.
"""

from __future__ import annotations

import io
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.graph import get_graph
from backend.state import GapGraphState

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

router = APIRouter()


def _extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from uploaded file (PDF or txt)."""
    if filename.lower().endswith(".pdf"):
        if PdfReader is None:
            raise HTTPException(
                status_code=400,
                detail="PyPDF2 not installed — cannot process PDF files.",
            )
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


@router.post("/analyze")
async def analyze(
    resume: UploadFile = File(..., description="Resume file (PDF or .txt)"),
    jd: str = Form(..., description="Job Description plain text"),
):
    """
    Full pipeline: Diagnose → Plan → Critique.
    Returns skill_gap_vector, roadmap DAG, reasoning_trace, and impact_metric.
    """
    raw_bytes = await resume.read()
    resume_text = _extract_text_from_file(raw_bytes, resume.filename or "resume.txt")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from resume.")
    if not jd.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    initial_state: GapGraphState = {
        "resume_text": resume_text,
        "jd_text": jd,
        "candidate_skills": [],
        "jd_skills": [],
        "skill_gap_vector": {},
        "roadmap_nodes": [],
        "roadmap_edges": [],
        "reasoning_trace": [],
        "critique_result": None,
        "impact_metric": 0.0,
        "retry_count": 0,
    }

    try:
        graph = get_graph()
        final_state: GapGraphState = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    return JSONResponse(
        content={
            "skill_gap_vector": final_state["skill_gap_vector"],
            "roadmap": {
                "nodes": final_state["roadmap_nodes"],
                "edges": final_state["roadmap_edges"],
            },
            "reasoning_trace": final_state["reasoning_trace"],
            "impact_metric": final_state["impact_metric"],
            "critique": final_state.get("critique_result"),
        }
    )


@router.post("/diagnose")
async def diagnose_only(
    resume: UploadFile = File(...),
    jd: str = Form(...),
):
    """Debug endpoint — runs Agent A only."""
    from backend.agents.diagnoser import diagnose as run_diagnose

    raw_bytes = await resume.read()
    resume_text = _extract_text_from_file(raw_bytes, resume.filename or "resume.txt")

    state: GapGraphState = {
        "resume_text": resume_text,
        "jd_text": jd,
        "candidate_skills": [],
        "jd_skills": [],
        "skill_gap_vector": {},
        "roadmap_nodes": [],
        "roadmap_edges": [],
        "reasoning_trace": [],
        "critique_result": None,
        "impact_metric": 0.0,
        "retry_count": 0,
    }
    result = run_diagnose(state)
    return {
        "candidate_skills": result["candidate_skills"],
        "jd_skills": result["jd_skills"],
        "skill_gap_vector": result["skill_gap_vector"],
    }


@router.post("/plan")
async def plan_only(
    resume: UploadFile = File(...),
    jd: str = Form(...),
):
    """Debug endpoint — runs Agent A + B."""
    from backend.agents.diagnoser import diagnose as run_diagnose
    from backend.agents.planner import plan as run_plan

    raw_bytes = await resume.read()
    resume_text = _extract_text_from_file(raw_bytes, resume.filename or "resume.txt")

    state: GapGraphState = {
        "resume_text": resume_text,
        "jd_text": jd,
        "candidate_skills": [],
        "jd_skills": [],
        "skill_gap_vector": {},
        "roadmap_nodes": [],
        "roadmap_edges": [],
        "reasoning_trace": [],
        "critique_result": None,
        "impact_metric": 0.0,
        "retry_count": 0,
    }
    state = run_diagnose(state)
    state = run_plan(state)
    return {
        "roadmap": {
            "nodes": state["roadmap_nodes"],
            "edges": state["roadmap_edges"],
        },
        "reasoning_trace": state["reasoning_trace"],
    }


@router.post("/critique")
async def critique_only(
    resume: UploadFile = File(...),
    jd: str = Form(...),
):
    """Debug endpoint — runs full pipeline up to critique."""
    from backend.agents.diagnoser import diagnose as run_diagnose
    from backend.agents.planner import plan as run_plan
    from backend.agents.critic import critique as run_critique

    raw_bytes = await resume.read()
    resume_text = _extract_text_from_file(raw_bytes, resume.filename or "resume.txt")

    state: GapGraphState = {
        "resume_text": resume_text,
        "jd_text": jd,
        "candidate_skills": [],
        "jd_skills": [],
        "skill_gap_vector": {},
        "roadmap_nodes": [],
        "roadmap_edges": [],
        "reasoning_trace": [],
        "critique_result": None,
        "impact_metric": 0.0,
        "retry_count": 0,
    }
    state = run_diagnose(state)
    state = run_plan(state)
    state = run_critique(state)
    return {
        "critique_result": state["critique_result"],
        "impact_metric": state["impact_metric"],
    }
