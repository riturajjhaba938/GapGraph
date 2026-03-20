"""
GapGraph FastAPI Application Entry Point
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.analyze import router as analyze_router

load_dotenv()

app = FastAPI(
    title="GapGraph — AI Adaptive Onboarding Engine",
    description=(
        "Bridges the gap between candidate resumes and job descriptions "
        "using a multi-agent LangGraph pipeline, NetworkX knowledge graph, "
        "and O*NET skill taxonomy. Returns a personalized, non-linear training roadmap."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for hackathon dev (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(analyze_router, prefix="", tags=["Pipeline"])


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "GapGraph API is running. Visit /docs for the interactive API.",
        "endpoints": ["/analyze", "/diagnose", "/plan", "/critique", "/health"],
    }
