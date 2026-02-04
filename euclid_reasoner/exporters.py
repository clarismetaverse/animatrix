from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .core import Angle, Segment
from .search import SearchResult


def _seg_id(seg: Segment) -> str:
    return f"seg:{seg}"


def _ang_id(ang: Angle) -> str:
    return f"ang:{ang.a}{ang.v}{ang.c}"


def result_to_hpg(result: SearchResult) -> dict:
    # --- spaces ---
    spaces = [
        {"id": "space:main", "label": "Main"},
        {"id": "space:equilateral", "label": "Equilateral"},
        {"id": "space:triangles", "label": "Triangles"},
        {"id": "space:congruence", "label": "Congruence"},
    ]

    # --- objects (minimal but useful) ---
    objects: List[dict] = []

    # Triangles as objects
    tri_objs: Dict[str, str] = {}
    for tri in result.state.triangles:
        oid = f"triangle:{tri.name}"
        tri_objs[tri.name] = oid
        objects.append(
            {
                "id": oid,
                "label": str(tri),
                "space": "space:triangles",
                "type": "triangle",
            }
        )

    # Segments / angles as objects (optional but helps graph navigation)
    # We'll add only those that appear in facts (eq_segs/eq_angs).
    seg_objs: Dict[str, str] = {}
    for s1, s2 in result.state.facts.eq_segs:
        for s in (s1, s2):
            sid = _seg_id(s)
            if sid not in seg_objs:
                seg_objs[sid] = sid
                objects.append(
                    {
                        "id": sid,
                        "label": str(s),
                        "space": "space:main",
                        "type": "segment",
                    }
                )

    ang_objs: Dict[str, str] = {}
    for a1, a2 in result.state.facts.eq_angs:
        for a in (a1, a2):
            aid = _ang_id(a)
            if aid not in ang_objs:
                ang_objs[aid] = aid
                objects.append(
                    {
                        "id": aid,
                        "label": str(a),
                        "space": "space:congruence",
                        "type": "angle",
                    }
                )

    # --- facts ---
    facts: List[dict] = []
    goal_fact_id: Optional[str] = None

    # OnRay facts
    onray_sorted = sorted(result.state.facts.on_rays, key=lambda r: (r.ray, r.point))
    for idx, fr in enumerate(onray_sorted, start=1):
        fid = f"fact:onray:{idx}"
        facts.append(
            {
                "id": fid,
                "label": f"OnRay({fr.point},{fr.ray})",
                "space": "space:main",
                "type": "OnRay",
            }
        )

    # EqSeg facts
    eqseg_sorted = sorted(result.state.facts.eq_segs, key=lambda p: (str(p[0]), str(p[1])))
    for idx, (s1, s2) in enumerate(eqseg_sorted, start=1):
        fid = f"fact:eqseg:{idx}"
        facts.append(
            {
                "id": fid,
                "label": f"EqSeg({s1},{s2})",
                "space": "space:main",
                "type": "EqSeg",
            }
        )

    # Congruent facts (from congruence set)
    congr_sorted = sorted(result.state.facts.congruent, key=lambda c: (c.t1.name, c.t2.name))
    for idx, c in enumerate(congr_sorted, start=1):
        fid = f"fact:congruent:{idx}"
        facts.append(
            {
                "id": fid,
                "label": f"Congruent({c.t1.name},{c.t2.name})",
                "space": "space:congruence",
                "type": "Congruent",
            }
        )

    # EqAng facts (+ detect goal)
    eqang_sorted = sorted(result.state.facts.eq_angs, key=lambda p: (str(p[0]), str(p[1])))
    eqang_fact_ids: Dict[Tuple[Angle, Angle], str] = {}
    for idx, (a1, a2) in enumerate(eqang_sorted, start=1):
        fid = f"fact:eqang:{idx}"
        eqang_fact_ids[(a1, a2)] = fid
        facts.append(
            {
                "id": fid,
                "label": f"EqAng({a1},{a2})",
                "space": "space:congruence",
                "type": "EqAng",
            }
        )

        if result.target and ((a1, a2) == result.target or (a2, a1) == result.target):
            goal_fact_id = fid

    # --- projections from hierarchical trace (HPG core) ---
    projections: List[dict] = []
    best_path: List[str] = []

    for i, step in enumerate(result.state.htrace, start=1):
        pid = f"proj:{i:03d}"
        best_path.append(pid)

        projections.append(
            {
                "id": pid,
                "operator": step.get("prism", f"Step{i}"),
                "label": step.get("label", step.get("prism", pid)),
                "space": step.get("space", "space:main"),
                # IMPORTANT: exporter expects "inputs" key, not "uses"
                "inputs": step.get("uses", []),
                # exporter expects these names
                "creates": step.get("creates", []),
                "asserts": step.get("asserts", []),
                "rewrites": step.get("rewrites", []),
            }
        )

    # Fallback: if nothing in htrace, at least add a single projection so exports don't break
    if not projections:
        projections.append(
            {
                "id": "proj:001",
                "operator": "NoTrace",
                "label": "No trace recorded",
                "space": "space:main",
                "inputs": [],
                "creates": [],
                "asserts": [],
                "rewrites": [],
            }
        )
        best_path = ["proj:001"]

    # --- query ---
    query = {
        "id": "query:goal",
        "label": "Goal",
    }
    if goal_fact_id:
        query["goal_fact_id"] = goal_fact_id

    return {
        "hpg_version": "1.0",
        "spaces": spaces,
        "objects": objects,
        "facts": facts,
        "projections": projections,
        "run": {"best_path_projection_ids": best_path},
        "query": query,
    }
