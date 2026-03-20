"""
Agent B — The Planner
Builds a NetworkX Knowledge Graph from catalog.json.
Performs Multi-Source Multi-Sink (MSMS) search to find the
minimal learning path from candidate's current skills to JD-required skills.
Applies skip logic: P(L₀) ≥ 0.85 → course skipped.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Set, Dict, Any

import networkx as nx

from backend.state import GapGraphState, RoadmapNode, RoadmapEdge, ReasoningStep

# ── Catalog loader ────────────────────────────────────────────────────────────
_CATALOG_PATH = Path(__file__).parent.parent.parent / "data" / "catalog.json"


def load_catalog() -> List[Dict]:
    with open(_CATALOG_PATH, "r") as f:
        return json.load(f)


# ── Knowledge Graph construction ──────────────────────────────────────────────

def build_knowledge_graph(catalog: List[Dict]) -> nx.DiGraph:
    """Build a directed acyclic graph: nodes = courses, edges = prerequisite → course."""
    G = nx.DiGraph()
    for course in catalog:
        G.add_node(
            course["uuid"],
            title=course["title"],
            skills_taught=course["skills_taught"],
            prerequisites=course["prerequisites"],
            level=course["level"],
            duration_hours=course["duration_hours"],
        )
    for course in catalog:
        for prereq_uuid in course["prerequisites"]:
            if prereq_uuid in G:
                G.add_edge(prereq_uuid, course["uuid"])
    return G


# ── MSMS Search ───────────────────────────────────────────────────────────────

def msms_search(G: nx.DiGraph, sink_uuids: Set[str]) -> Set[str]:
    """
    Multi-Source Multi-Sink search.
    Finds all courses needed to reach sink_uuids, by traversing predecessors
    (topological ancestors) for each sink.
    Returns the union of all ancestor course uuids + the sinks themselves.
    """
    required_nodes: Set[str] = set()
    for sink in sink_uuids:
        if sink not in G:
            continue
        # All ancestors (transitive prerequisites)
        ancestors = nx.ancestors(G, sink)
        required_nodes.update(ancestors)
        required_nodes.add(sink)
    return required_nodes


# ── Main agent function ────────────────────────────────────────────────────────

def plan(state: GapGraphState) -> GapGraphState:
    """
    Agent B: Build the personalized roadmap DAG.
    Updates: roadmap_nodes, roadmap_edges, reasoning_trace (partial).
    """
    candidate_skills = state["candidate_skills"]
    jd_skills = state["jd_skills"]
    skill_gap_vector = state["skill_gap_vector"]

    catalog = load_catalog()
    G = build_knowledge_graph(catalog)

    # Index courses by O*NET code → uuid
    onet_to_courses: Dict[str, List[str]] = {}
    for uuid, data in G.nodes(data=True):
        for onet_code in data.get("skills_taught", []):
            onet_to_courses.setdefault(onet_code, []).append(uuid)

    # Determine candidate's mastery map: onet_code → mastery_prob
    candidate_mastery: Dict[str, float] = {
        s["onet_code"]: s["mastery_prob"] for s in candidate_skills
    }

    # Target sinks: courses teaching skills with a positive gap
    sink_uuids: Set[str] = set()
    for skill_name, gap_info in skill_gap_vector.items():
        if gap_info["gap"] > 0:  # candidate lacks this skill
            onet_code = gap_info["onet_code"]
            for uuid in onet_to_courses.get(onet_code, []):
                sink_uuids.add(uuid)

    # If no gaps, provide all courses as broad roadmap
    if not sink_uuids:
        sink_uuids = set(G.nodes())

    # MSMS search: find all required courses
    required_uuids = msms_search(G, sink_uuids)

    # Apply skip logic + build reasoning trace
    roadmap_nodes: List[RoadmapNode] = []
    reasoning_trace: List[ReasoningStep] = []
    trace_step_counter = [1]  # mutable counter

    topo_order = list(nx.topological_sort(G))

    for uuid in topo_order:
        if uuid not in required_uuids:
            continue

        node_data = G.nodes[uuid]
        skills_taught = node_data.get("skills_taught", [])

        # Determine if this course can be skipped
        # A course is skipped if the candidate has high mastery for ALL skills it teaches
        mastery_scores = [candidate_mastery.get(s, 0.0) for s in skills_taught]
        avg_mastery = sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0.0
        skipped = avg_mastery >= 0.85

        # Build 4-step reasoning trace for this node
        gap_skills = [
            name for name, info in skill_gap_vector.items()
            if info["onet_code"] in skills_taught and info["gap"] > 0
        ]
        target_skill_desc = ", ".join(gap_skills) if gap_skills else "General prerequisite"

        prereq_names = []
        for prereq_uuid in node_data.get("prerequisites", []):
            if prereq_uuid in G:
                prereq_names.append(G.nodes[prereq_uuid].get("title", prereq_uuid))

        prereq_desc = ", ".join(prereq_names) if prereq_names else "None"
        action = "SKIP — candidate already has sufficient mastery" if skipped else f"INCLUDE in roadmap"

        trace: List[ReasoningStep] = [
            ReasoningStep(step=1, label="Target Skill", description=target_skill_desc),
            ReasoningStep(step=2, label="Catalog Match", description=f"Found '{node_data['title']}' ({uuid})"),
            ReasoningStep(step=3, label="Dependency Check", description=f"Prerequisites: {prereq_desc}"),
            ReasoningStep(step=4, label="Final Action", description=action),
        ]
        reasoning_trace.extend(trace)

        roadmap_nodes.append(
            RoadmapNode(
                uuid=uuid,
                title=node_data["title"],
                skipped=skipped,
                level=node_data["level"],
                duration_hours=node_data["duration_hours"],
                skills_taught=skills_taught,
                trace=trace,
            )
        )

    # Build roadmap edges (only between nodes in the roadmap)
    roadmap_uuid_set = {n["uuid"] for n in roadmap_nodes}
    roadmap_edges: List[RoadmapEdge] = []
    for src, tgt in G.edges():
        if src in roadmap_uuid_set and tgt in roadmap_uuid_set:
            roadmap_edges.append(RoadmapEdge(source=src, target=tgt))

    return {
        **state,
        "roadmap_nodes": roadmap_nodes,
        "roadmap_edges": roadmap_edges,
        "reasoning_trace": reasoning_trace,
    }
