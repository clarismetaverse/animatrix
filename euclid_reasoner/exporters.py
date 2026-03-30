from __future__ import annotations

from typing import List, Set

from .types import SearchResult


def result_to_hpg(result: SearchResult) -> dict:
    state = result.state

    node_ids: Set[str] = set()
    nodes: List[dict] = []
    edges: List[dict] = []

    def add_node(node_id: str, label: str, node_type: str) -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append({"id": node_id, "label": label, "type": node_type})

    # Space nodes
    for step in state.htrace:
        add_node(step.space, step.space, "space")

    # Projection nodes and semantic relations
    for step in state.htrace:
        projection_id = f"projection:{step.id}"
        add_node(projection_id, step.label, "projection")
        edges.append({"from": projection_id, "to": step.space, "type": "in_space"})

        for used in step.uses:
            add_node(used, used, "entity")
            edges.append({"from": projection_id, "to": used, "type": "uses"})

        for created in step.creates:
            add_node(created, created, "entity")
            edges.append({"from": projection_id, "to": created, "type": "creates"})

        for asserted in step.asserts:
            fact_id = f"fact:{asserted}"
            add_node(fact_id, asserted, "fact")
            edges.append({"from": projection_id, "to": fact_id, "type": "asserts"})

        for rewritten in step.rewrites:
            fact_id = f"fact:{rewritten}"
            add_node(fact_id, rewritten, "fact")
            edges.append({"from": projection_id, "to": fact_id, "type": "rewrites"})

        for parent in step.parents:
            parent_projection_id = f"projection:{parent}"
            add_node(parent_projection_id, parent, "projection")
            edges.append({"from": parent_projection_id, "to": projection_id, "type": "derives"})

    return {"nodes": nodes, "edges": edges}
