from __future__ import annotations

from typing import Optional, Tuple

from .core import Angle
from .hpg_model import (
    ASSERTS,
    CREATES,
    DERIVES,
    IN_SPACE,
    INTERPRETS,
    REWRITES,
    SHADOW_OF,
    SUPPORTS_GOAL,
    USES,
    FactNode,
    HPGEdge,
    HPGGraph,
    ObjectNode,
    ProjectionNode,
    QueryNode,
    SpaceNode,
    ViewNode,
)
from .types import SearchResult


def _extract_object_kind(entity: str) -> Optional[str]:
    for prefix in ("triangle:", "point:", "segment:", "angle:"):
        if entity.startswith(prefix):
            return prefix[:-1]
    return None


def _ensure_object_and_view(graph: HPGGraph, *, entity: str, space: str) -> str:
    kind = _extract_object_kind(entity)
    if kind is None:
        view_id = f"view:{space}:{entity}:generic"
        graph.add_node(
            ViewNode(
                id=view_id,
                label=f"{entity}@generic",
                type="view",
                meta={"space": space, "role": "generic", "entity": entity},
            )
        )
        return view_id

    object_id = f"object:{entity}"
    graph.add_node(ObjectNode(id=object_id, label=entity, type="object", meta={"object_type": kind}))

    view_id = f"view:{space}:{entity}:generic"
    graph.add_node(
        ViewNode(
            id=view_id,
            label=f"{entity}@generic",
            type="view",
            meta={"space": space, "role": "generic", "object": object_id},
        )
    )
    graph.add_edge(HPGEdge(from_id=view_id, to_id=object_id, type=INTERPRETS))
    graph.add_edge(HPGEdge(from_id=view_id, to_id=object_id, type=SHADOW_OF))
    return view_id


def _fact_matches_target(fact_label: str, target: Optional[Tuple[Angle, Angle]]) -> bool:
    if target is None:
        return False
    ang1, ang2 = target
    a1 = str(ang1)
    a2 = str(ang2)
    return fact_label.startswith("EqAng(") and a1 in fact_label and a2 in fact_label


def result_to_hpg(result: SearchResult) -> dict:
    state = result.state
    graph = HPGGraph()

    query_id = "query:goal"
    graph.add_node(QueryNode(id=query_id, label="Goal", type="query"))

    for step in state.htrace:
        graph.add_node(SpaceNode(id=step.space, label=step.space, type="space"))

    for step in state.htrace:
        projection_id = f"projection:{step.id}"
        graph.add_node(ProjectionNode(id=projection_id, label=step.label, type="projection", meta={"prism": step.prism}))
        graph.add_edge(HPGEdge(from_id=projection_id, to_id=step.space, type=IN_SPACE))

        for used in step.uses:
            view_id = _ensure_object_and_view(graph, entity=used, space=step.space)
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=view_id, type=USES))

        for created in step.creates:
            view_id = _ensure_object_and_view(graph, entity=created, space=step.space)
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=view_id, type=CREATES))

        for asserted in step.asserts:
            fact_id = f"fact:{asserted}"
            graph.add_node(FactNode(id=fact_id, label=asserted, type="fact"))
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=ASSERTS))
            if _fact_matches_target(asserted, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for rewritten in step.rewrites:
            fact_id = f"fact:{rewritten}"
            graph.add_node(FactNode(id=fact_id, label=rewritten, type="fact"))
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=REWRITES))
            if _fact_matches_target(rewritten, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for parent in step.parents:
            parent_projection_id = f"projection:{parent}"
            graph.add_node(ProjectionNode(id=parent_projection_id, label=parent, type="projection"))
            graph.add_edge(HPGEdge(from_id=parent_projection_id, to_id=projection_id, type=DERIVES))

    return graph.to_dict()


def hpg_to_graph_json(hpg: dict) -> dict:
    return {"nodes": hpg.get("nodes", []), "edges": hpg.get("edges", [])}


def hpg_to_opml(hpg: dict) -> str:
    node_labels = {node["id"]: node.get("label", node["id"]) for node in hpg.get("nodes", [])}
    projections = [node for node in hpg.get("nodes", []) if node.get("type") == "projection"]
    facts = [node for node in hpg.get("nodes", []) if node.get("type") == "fact"]

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        '  <head><title>Euclid Reasoner HPG</title></head>',
        '  <body>',
        '    <outline text="Goal">',
    ]

    for edge in hpg.get("edges", []):
        if edge.get("type") == SUPPORTS_GOAL:
            lines.append(f'      <outline text="{node_labels.get(edge["from"], edge["from"])}"/>')

    lines.append("    </outline>")
    lines.append('    <outline text="Projections">')
    for projection in projections:
        lines.append(f'      <outline text="{projection.get("label", projection["id"])}"/>')
    lines.append("    </outline>")
    lines.append('    <outline text="Facts">')
    for fact in facts:
        lines.append(f'      <outline text="{fact.get("label", fact["id"])}"/>')
    lines.extend(["    </outline>", "  </body>", "</opml>"])
    return "\n".join(lines)
