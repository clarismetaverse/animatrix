from __future__ import annotations

from typing import List, Dict

from .types import SearchResult


def result_to_hpg(result: SearchResult) -> dict:
    state = result.state

    nodes: List[dict] = []
    edges: List[dict] = []

    # --- nodes: triangles ---
    for tri in state.triangles:
        nodes.append({
            "id": f"triangle:{tri.name}",
            "label": str(tri),
            "type": "triangle",
        })

    # --- nodes: angles ---
    for a1, a2 in state.facts.eq_angs:
        nodes.append({
            "id": f"eqang:{str(a1)}-{str(a2)}",
            "label": f"{a1}={a2}",
            "type": "eq_ang",
        })

    # --- trace → projections ---
    for i, step in enumerate(state.trace):
        node_id = f"step:{i}"
        nodes.append({
            "id": node_id,
            "label": step,
            "type": "step",
        })

        if i > 0:
            edges.append({
                "from": f"step:{i-1}",
                "to": node_id,
                "type": "sequence",
            })

    return {
        "nodes": nodes,
        "edges": edges,
    }
