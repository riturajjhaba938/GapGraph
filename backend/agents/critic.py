"""
Agent C — The Critic
Validates the roadmap DAG produced by Agent B:
  1. All course UUIDs exist in catalog.json
  2. All prerequisite edges are valid
  3. Flags hallucinated courses
  4. Verifies 4-step reasoning trace format per node
  5. Computes impact_metric = (skipped / total) * 100
  6. Returns a CritiqueReport (passed | failed)

If failed → LangGraph routes back to Agent B for re-planning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set

from backend.state import GapGraphState, CritiqueReport

# ── Catalog loader ────────────────────────────────────────────────────────────
_CATALOG_PATH = Path(__file__).parent.parent.parent / "data" / "catalog.json"


def _load_valid_uuids() -> Dict[str, Dict]:
    with open(_CATALOG_PATH, "r") as f:
        catalog = json.load(f)
    return {c["uuid"]: c for c in catalog}


# ── Main agent function ────────────────────────────────────────────────────────

def critique(state: GapGraphState) -> GapGraphState:
    """
    Agent C: Validate the roadmap and compute impact metric.
    Updates: critique_result, impact_metric.
    """
    roadmap_nodes = state.get("roadmap_nodes", [])
    roadmap_edges = state.get("roadmap_edges", [])

    catalog_map = _load_valid_uuids()
    valid_uuids: Set[str] = set(catalog_map.keys())

    hallucination_flags = []
    missing_prerequisites = []
    trace_errors = []

    roadmap_uuid_set: Set[str] = {n["uuid"] for n in roadmap_nodes}

    # 1. Check all nodes exist in catalog
    for node in roadmap_nodes:
        uuid = node["uuid"]
        if uuid not in valid_uuids:
            hallucination_flags.append(uuid)

    # 2. Check all edges are valid (both endpoints exist in catalog)
    for edge in roadmap_edges:
        src = edge["source"]
        tgt = edge["target"]
        if src not in valid_uuids or tgt not in valid_uuids:
            missing_prerequisites.append(f"{src} → {tgt}")
        else:
            # Verify the edge is actually a defined prerequisite relationship
            catalog_prereqs = catalog_map.get(tgt, {}).get("prerequisites", [])
            if src not in catalog_prereqs:
                missing_prerequisites.append(
                    f"{src} → {tgt} (not a valid prerequisite in catalog)"
                )

    # 3. Verify reasoning trace format: must have exactly 4 steps per node
    for node in roadmap_nodes:
        trace = node.get("trace", [])
        if len(trace) != 4:
            trace_errors.append(
                f"Node {node['uuid']} has {len(trace)} trace steps (expected 4)"
            )
        else:
            for step in trace:
                if step.get("step") not in (1, 2, 3, 4):
                    trace_errors.append(
                        f"Node {node['uuid']} trace step has invalid step number: {step.get('step')}"
                    )

    # 4. Calculate impact metric
    total = len(roadmap_nodes)
    skipped = sum(1 for n in roadmap_nodes if n.get("skipped", False))
    impact_metric = round((skipped / total * 100) if total > 0 else 0.0, 2)

    # 5. Determine pass/fail
    all_ok = (
        len(hallucination_flags) == 0
        and len(missing_prerequisites) == 0
        and len(trace_errors) == 0
    )

    if all_ok:
        message = (
            f"Roadmap validated successfully. "
            f"{total} courses ({skipped} skipped). "
            f"Impact metric: {impact_metric}% curriculum bypassed."
        )
    else:
        parts = []
        if hallucination_flags:
            parts.append(f"Hallucinated courses: {hallucination_flags}")
        if missing_prerequisites:
            parts.append(f"Invalid prerequisites: {missing_prerequisites}")
        if trace_errors:
            parts.append(f"Trace format errors: {trace_errors}")
        message = " | ".join(parts)

    critique_result = CritiqueReport(
        passed=all_ok,
        hallucination_flags=hallucination_flags,
        missing_prerequisites=missing_prerequisites,
        message=message,
    )

    return {
        **state,
        "critique_result": critique_result,
        "impact_metric": impact_metric,
    }


def route_critique(state: GapGraphState) -> str:
    """LangGraph conditional edge: 'pass' → END, 'fail' → 'plan' (re-plan)."""
    critique_result = state.get("critique_result")
    retry_count = state.get("retry_count", 0)

    # Guard: don't loop forever
    if retry_count >= 2:
        return "pass"

    if critique_result and critique_result.get("passed"):
        return "pass"

    # Increment retry count in state (handled in graph.py via state update)
    return "fail"
