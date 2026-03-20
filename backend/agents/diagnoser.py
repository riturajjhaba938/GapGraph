"""
Agent A — The Diagnoser
Extracts skills from resume + JD, normalizes to O*NET codes,
computes initial mastery probability P(L₀), builds Skill-Gap Vector.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

# ── O*NET taxonomy (local fallback) ─────────────────────────────────────────
_TAXONOMY_PATH = Path(__file__).parent.parent.parent / "data" / "onet_taxonomy.json"

def _load_taxonomy() -> Dict[str, str]:
    with open(_TAXONOMY_PATH, "r") as f:
        return json.load(f)

ONET_TAXONOMY: Dict[str, str] = _load_taxonomy()


def normalize_to_onet(skill_name: str) -> str:
    """Map a raw skill string to an O*NET code. Case-insensitive fuzzy match."""
    # Exact match first
    if skill_name in ONET_TAXONOMY:
        return ONET_TAXONOMY[skill_name]
    # Case-insensitive
    lower = skill_name.lower()
    for key, code in ONET_TAXONOMY.items():
        if key.lower() == lower:
            return code
    # Substring match
    for key, code in ONET_TAXONOMY.items():
        if key.lower() in lower or lower in key.lower():
            return code
    # Default: generate a synthetic code from skill name
    slug = re.sub(r"[^a-z0-9]", "-", lower)[:20]
    return f"ONET-CUSTOM-{slug}"


def compute_mastery_prob(years: float, frequency_score: float = 1.0) -> float:
    """
    P(L₀) = min(1.0, (years / 3) * skill_frequency_score)
    frequency_score: how frequently the skill appears in the resume (default 1.0)
    """
    return min(1.0, (years / 3.0) * frequency_score)


# ── LLM-based extraction (OpenAI) ────────────────────────────────────────────
def _extract_skills_with_llm(text: str, mode: str) -> List[Dict]:
    """
    Use OpenAI GPT-4o to extract skills from resume or JD text.
    Returns a list of dicts: [{name, years_experience|required_level}]
    Falls back to regex if API key not set.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-...":
        return _extract_skills_regex(text, mode)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        if mode == "resume":
            prompt = f"""Extract ALL technical skills from this resume text. 
For each skill, estimate years of experience (0 if unclear).
Return ONLY valid JSON array: [{{"name": "Docker", "years_experience": 2.0}}, ...]

Resume text:
{text[:3000]}"""
        else:
            prompt = f"""Extract ALL required technical skills from this job description.
For each skill, estimate the required proficiency level (0.0-1.0, where 1.0 = expert).
Return ONLY valid JSON array: [{{"name": "Docker", "required_level": 0.8}}, ...]

Job description:
{text[:3000]}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"[Diagnoser] LLM extraction failed ({e}), falling back to regex.")
        return _extract_skills_regex(text, mode)


def _extract_skills_regex(text: str, mode: str) -> List[Dict]:
    """Simple regex-based skill extraction as fallback."""
    skill_keywords = list(ONET_TAXONOMY.keys())
    found = []
    seen = set()
    text_lower = text.lower()

    for skill in skill_keywords:
        if skill.lower() in text_lower and skill not in seen:
            seen.add(skill)
            if mode == "resume":
                # Estimate years from context (very rough)
                yrs = 1.0
                match = re.search(
                    rf"(\d+)\+?\s*(?:year|yr)s?\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?{re.escape(skill.lower())}",
                    text_lower
                )
                if match:
                    yrs = float(match.group(1))
                found.append({"name": skill, "years_experience": yrs})
            else:
                found.append({"name": skill, "required_level": 0.7})

    return found


# ── Main agent function ───────────────────────────────────────────────────────
from backend.state import GapGraphState, NormalizedSkill


def diagnose(state: GapGraphState) -> GapGraphState:
    """
    Agent A: Diagnose skill gaps between resume and JD.
    Updates: candidate_skills, jd_skills, skill_gap_vector.
    """
    resume_text = state["resume_text"]
    jd_text = state["jd_text"]

    # 1. Extract raw skills
    raw_candidate = _extract_skills_with_llm(resume_text, "resume")
    raw_jd = _extract_skills_with_llm(jd_text, "jd")

    # 2. Normalize to O*NET codes + compute mastery
    candidate_skills: List[NormalizedSkill] = []
    for item in raw_candidate:
        name = item.get("name", "")
        yrs = float(item.get("years_experience", 1.0))
        onet = normalize_to_onet(name)
        prob = compute_mastery_prob(yrs)
        candidate_skills.append(
            NormalizedSkill(
                name=name,
                onet_code=onet,
                years_experience=yrs,
                required_level=0.0,
                mastery_prob=prob,
            )
        )

    jd_skills: List[NormalizedSkill] = []
    for item in raw_jd:
        name = item.get("name", "")
        level = float(item.get("required_level", 0.7))
        onet = normalize_to_onet(name)
        jd_skills.append(
            NormalizedSkill(
                name=name,
                onet_code=onet,
                years_experience=0.0,
                required_level=level,
                mastery_prob=0.0,
            )
        )

    # 3. Build Skill-Gap Vector
    # Index candidate skills by O*NET code
    candidate_map: Dict[str, float] = {s["onet_code"]: s["mastery_prob"] for s in candidate_skills}

    skill_gap_vector: Dict[str, Dict[str, float]] = {}
    for skill in jd_skills:
        code = skill["onet_code"]
        name = skill["name"]
        candidate_level = candidate_map.get(code, 0.0)
        required_level = skill["required_level"]
        gap = required_level - candidate_level
        skill_gap_vector[name] = {
            "onet_code": code,
            "candidate": round(candidate_level, 3),
            "required": round(required_level, 3),
            "gap": round(gap, 3),
        }

    return {
        **state,
        "candidate_skills": candidate_skills,
        "jd_skills": jd_skills,
        "skill_gap_vector": skill_gap_vector,
    }
