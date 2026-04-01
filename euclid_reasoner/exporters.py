from __future__ import annotations

from typing import Optional, Tuple

from .core import Angle
from .hpg_model import (
    ASSERTS,
    CREATES,
    DERIVES,
    EXPLORES,
    IN_SPACE,
    INTERPRETS,
    REINTERPRETS,
    REWRITES,
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


def _infer_fact_type(fact_label: str) -> str:
    for prefix in ("EqSeg(", "EqAng(", "Congruent(", "OnRay("):
        if fact_label.startswith(prefix):
            return prefix[:-1]
    return "Fact"


def _infer_base_role(entity: str) -> str:
    if entity.startswith("triangle:"):
        return "triangle_instance"
    if entity.startswith("point:"):
        return "point_object"
    if entity.startswith("segment:"):
        return "segment_object"
    if entity.startswith("angle:"):
        return "angle_object"
    return "generic"


def _infer_role(entity: str, space: str) -> str:
    kind = _extract_object_kind(entity)
    role = _infer_base_role(entity)

    if space == "triangle_space":
        if kind == "triangle":
            return "triangle_instance"
        if kind == "segment":
            return "triangle_side_candidate"
        if kind == "point":
            return "triangle_vertex_candidate"
    if space == "equilateral_space":
        if kind == "segment":
            return "equal_side_candidate"
        if kind == "point":
            return "equilateral_vertex_candidate"
    if space == "congruence_space":
        if kind == "segment":
            return "congruence_participant"
        if kind == "triangle":
            return "congruence_triangle"
        if kind == "angle":
            return "congruence_angle"
    if space == "construction_space":
        if kind == "point":
            return "constructed_point"
        if kind == "segment":
            return "constructed_segment"

    return role


def _is_fact_like_entity(entity: str) -> bool:
    return any(token in entity for token in ("Congruent(", "EqSeg(", "EqAng(", "OnRay("))


def _ensure_object_and_view(graph: HPGGraph, *, entity: str, space: str) -> str:
    if _is_fact_like_entity(entity):
        return ""

    kind = _extract_object_kind(entity)
    role = _infer_role(entity, space)
    if kind is None:
        object_id = f"object:{entity}"
        graph.add_node(ObjectNode(id=object_id, label=entity, object_type="unknown"))
        view_id = f"view:{space}:{entity}:{role}"
        graph.add_node(
            ViewNode(
                id=view_id,
                label=f"{entity}@{role}",
                role=role,
                object_id=object_id,
                space_id=space,
                meta={"entity": entity},
            )
        )
        graph.add_edge(HPGEdge(from_id=view_id, to_id=object_id, type=INTERPRETS))
        return view_id

    object_id = f"object:{entity}"
    graph.add_node(ObjectNode(id=object_id, label=entity, object_type=kind))

    view_id = f"view:{space}:{entity}:{role}"
    graph.add_node(
            ViewNode(
                id=view_id,
                label=f"{entity}@{role}",
                role=role,
                object_id=object_id,
                space_id=space,
        )
    )
    graph.add_edge(HPGEdge(from_id=view_id, to_id=object_id, type=INTERPRETS))
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
    graph.add_node(QueryNode(id=query_id, label="Goal"))

    for step in state.htrace:
        graph.add_node(SpaceNode(id=step.space, label=step.space))

    latest_view_by_object: dict[str, tuple[str, str]] = {}

    for step in state.htrace:
        projection_id = f"projection:{step.id}"
        graph.add_node(
            ProjectionNode(
                id=projection_id,
                label=step.label,
                projection_type=step.prism,
                space_id=step.space,
            )
        )
        graph.add_edge(HPGEdge(from_id=projection_id, to_id=step.space, type=IN_SPACE))

        for used in step.uses:
            view_id = _ensure_object_and_view(graph, entity=used, space=step.space)
            if not view_id:
                continue
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=view_id, type=USES))

        for created in step.creates:
            view_id = _ensure_object_and_view(graph, entity=created, space=step.space)
            if not view_id:
                continue
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=view_id, type=CREATES))
            object_id = f"object:{created}"
            if object_id in latest_view_by_object:
                old_view_id, old_space = latest_view_by_object[object_id]
                if old_space != step.space and old_view_id != view_id:
                    graph.add_edge(HPGEdge(from_id=view_id, to_id=old_view_id, type=REINTERPRETS))
            latest_view_by_object[object_id] = (view_id, step.space)

        for used in step.uses:
            object_id = f"object:{used}"
            current_view_id = _ensure_object_and_view(graph, entity=used, space=step.space)
            if not current_view_id or object_id not in latest_view_by_object:
                continue
            old_view_id, old_space = latest_view_by_object[object_id]
            if old_space != step.space and old_view_id != current_view_id:
                graph.add_edge(HPGEdge(from_id=current_view_id, to_id=old_view_id, type=EXPLORES))
            latest_view_by_object[object_id] = (current_view_id, step.space)

        for asserted in step.asserts:
            fact_id = f"fact:{asserted}"
            graph.add_node(
                FactNode(
                    id=fact_id,
                    label=asserted,
                    fact_type=_infer_fact_type(asserted),
                    space_id=step.space,
                )
            )
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=ASSERTS))
            if _fact_matches_target(asserted, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for rewritten in step.rewrites:
            fact_id = f"fact:{rewritten}"
            graph.add_node(
                FactNode(
                    id=fact_id,
                    label=rewritten,
                    fact_type=_infer_fact_type(rewritten),
                    space_id=step.space,
                )
            )
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=REWRITES))
            if _fact_matches_target(rewritten, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for parent in step.parents:
            parent_projection_id = f"projection:{parent}"
            graph.add_node(ProjectionNode(id=parent_projection_id, label=parent))
            graph.add_edge(HPGEdge(from_id=parent_projection_id, to_id=projection_id, type=DERIVES))

    return graph.to_dict()


def hpg_to_graph_json(hpg: dict) -> dict:
    return {"nodes": hpg.get("nodes", []), "edges": hpg.get("edges", [])}


def hpg_to_opml(hpg: dict) -> str:
    node_labels = {node["id"]: node.get("label", node["id"]) for node in hpg.get("nodes", [])}
    projections = [node for node in hpg.get("nodes", []) if node.get("kind") == "projection"]
    facts = [node for node in hpg.get("nodes", []) if node.get("kind") == "fact"]

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
