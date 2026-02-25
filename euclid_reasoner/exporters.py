from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .core import Angle, Segment
from .types import SearchResult


def _seg_id(seg: Segment) -> str:
    return f"seg:{seg}"


def _ang_id(ang: Angle) -> str:
    return f"ang:{ang.a}{ang.v}{ang.c}"


def result_to_hpg(result: SearchResult) -> dict:
    spaces = [
        {"id": "space:main", "label": "Main"},
        {"id": "space:equilateral", "label": "Equilateral"},
        {"id": "space:triangles", "label": "Triangles"},
        {"id": "space:congruence", "label": "Congruence"},
    ]

    objects: List[dict] = []

    for tri in result.state.triangles:
        objects.append(
            {
                "id": f"triangle:{tri.name}",
                "label": str(tri),
                "space": "space:triangles",
                "type": "triangle",
            }
        )

    seg_objs: Dict[str, str] = {}
    for s1, s2 in result.state.facts.eq_segs:
        for seg in (s1, s2):
            sid = _seg_id(seg)
            if sid not in seg_objs:
                seg_objs[sid] = sid
                objects.append(
                    {
                        "id": sid,
                        "label": str(seg),
                        "space": "space:main",
                        "type": "segment",
                    }
                )

    ang_objs: Dict[str, str] = {}
    for a1, a2 in result.state.facts.eq_angs:
        for ang in (a1, a2):
            aid = _ang_id(ang)
            if aid not in ang_objs:
                ang_objs[aid] = aid
                objects.append(
                    {
                        "id": aid,
                        "label": str(ang),
                        "space": "space:congruence",
                        "type": "angle",
                    }
                )

    facts: List[dict] = []
    goal_fact_id: Optional[str] = None

    onray_sorted = sorted(result.state.facts.on_rays, key=lambda r: (r.ray, r.point))
    for idx, fr in enumerate(onray_sorted, start=1):
        facts.append(
            {
                "id": f"fact:onray:{idx}",
                "label": f"OnRay({fr.point},{fr.ray})",
                "space": "space:main",
                "type": "OnRay",
            }
        )

    eqseg_sorted = sorted(result.state.facts.eq_segs, key=lambda p: (str(p[0]), str(p[1])))
    for idx, (s1, s2) in enumerate(eqseg_sorted, start=1):
        facts.append(
            {
                "id": f"fact:eqseg:{idx}",
                "label": f"EqSeg({s1},{s2})",
                "space": "space:main",
                "type": "EqSeg",
            }
        )

    congr_sorted = sorted(result.state.facts.congruent, key=lambda c: (c.t1.name, c.t2.name))
    for idx, c in enumerate(congr_sorted, start=1):
        facts.append(
            {
                "id": f"fact:congruent:{idx}",
                "label": f"Congruent({c.t1.name},{c.t2.name})",
                "space": "space:congruence",
                "type": "Congruent",
            }
        )

    eqang_sorted = sorted(result.state.facts.eq_angs, key=lambda p: (str(p[0]), str(p[1])))
    for idx, (a1, a2) in enumerate(eqang_sorted, start=1):
        fid = f"fact:eqang:{idx}"
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

    projections: List[dict] = []
    best_path: List[str] = []
    for idx, step in enumerate(result.state.htrace, start=1):
        pid = f"proj:{idx:03d}"
        best_path.append(pid)
        projections.append(
            {
                "id": pid,
                "operator": step.get("prism", f"Step{idx}"),
                "label": step.get("label", step.get("prism", pid)),
                "space": step.get("space", "space:main"),
                "inputs": step.get("uses", []),
                "creates": step.get("creates", []),
                "asserts": step.get("asserts", []),
                "rewrites": step.get("rewrites", []),
            }
        )

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

    query = {"id": "query:goal", "label": "Goal"}
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


def hpg_to_graph_json(hpg: dict) -> dict:
    nodes = []
    edges = []

    for space in hpg.get("spaces", []):
        nodes.append({"id": space["id"], "label": space["label"], "kind": "space"})

    for obj in hpg.get("objects", []):
        nodes.append({"id": obj["id"], "label": obj["label"], "kind": obj.get("type", "object")})
        if obj.get("space"):
            edges.append({"from": obj["id"], "to": obj["space"], "type": "shadow_of"})

    for fact in hpg.get("facts", []):
        nodes.append({"id": fact["id"], "label": fact["label"], "kind": fact.get("type", "fact")})
        if fact.get("space"):
            edges.append({"from": fact["id"], "to": fact["space"], "type": "shadow_of"})

    for proj in hpg.get("projections", []):
        pid = proj["id"]
        nodes.append({"id": pid, "label": proj.get("label", pid), "kind": "projection"})
        if proj.get("space"):
            edges.append({"from": pid, "to": proj["space"], "type": "shadow_of"})

        for source in proj.get("inputs", []):
            edges.append({"from": source, "to": pid, "type": "uses"})
        for created in proj.get("creates", []):
            edges.append({"from": pid, "to": created, "type": "creates"})
        for asserted in proj.get("asserts", []):
            edges.append({"from": pid, "to": asserted, "type": "asserts"})
        for rewritten in proj.get("rewrites", []):
            edges.append({"from": pid, "to": rewritten, "type": "rewrites"})

    return {"nodes": nodes, "edges": edges}


def hpg_to_opml(hpg: dict) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        "  <head>",
        "    <title>Euclid Reasoner Export</title>",
        "  </head>",
        "  <body>",
        '    <outline text="Goal"/>',
    ]

    for proj in hpg.get("projections", []):
        label = proj.get("label", proj.get("operator", proj.get("id", "Projection")))
        safe_label = (
            str(label)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        lines.append(f'    <outline text="{safe_label}"/>')

    lines.extend(["  </body>", "</opml>"])
    return "\n".join(lines)
