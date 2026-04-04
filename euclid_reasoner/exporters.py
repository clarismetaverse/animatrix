from __future__ import annotations

from typing import Dict, Optional, Set, Tuple

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


def _parse_eqseg_fact(label: str) -> Tuple[str, str]:
    inner = label[len("EqSeg(") : -1]
    left, right = [part.strip() for part in inner.split(",", 1)]
    return left, right


def _parse_eqang_fact(label: str) -> Tuple[str, str]:
    inner = label[len("EqAng(") : -1]
    left, right = [part.strip() for part in inner.split(",", 1)]
    return left, right


def _fact_id(label: str) -> str:
    return f"fact:{label}"


def _add_fact_node(
    graph: HPGGraph,
    *,
    label: str,
    space_id: str,
    origin: str,
    derived_from: Optional[Set[str]] = None,
) -> None:
    meta: Dict[str, str] = {"origin": origin, "space_id": space_id}
    if derived_from:
        meta["derived_from"] = "|".join(sorted(derived_from))
    graph.add_node(
        FactNode(
            id=_fact_id(label),
            label=label,
            fact_type=_infer_fact_type(label),
            space_id=space_id,
            meta=meta,
        )
    )


def _materialize_final_entities(graph: HPGGraph, result: SearchResult) -> None:
    state = result.state
    graph.add_node(SpaceNode(id="fact_space", label="fact_space"))

    for on_ray in state.facts.on_rays:
        _ensure_object_and_view(graph, entity=f"point:{on_ray.point}", space="fact_space")
    for seg1, seg2 in state.facts.eq_segs:
        _ensure_object_and_view(graph, entity=f"segment:{seg1}", space="fact_space")
        _ensure_object_and_view(graph, entity=f"segment:{seg2}", space="fact_space")
    for tri in state.triangles:
        _ensure_object_and_view(graph, entity=f"triangle:{tri.name}", space="fact_space")
    for ang1, ang2 in state.facts.eq_angs:
        _ensure_object_and_view(graph, entity=f"angle:{ang1}", space="fact_space")
        _ensure_object_and_view(graph, entity=f"angle:{ang2}", space="fact_space")
    if result.target is not None:
        t1, t2 = result.target
        _ensure_object_and_view(graph, entity=f"angle:{t1}", space="fact_space")
        _ensure_object_and_view(graph, entity=f"angle:{t2}", space="fact_space")


def result_to_hpg(result: SearchResult) -> dict:
    state = result.state
    graph = HPGGraph()

    query_id = "query:goal"
    query_label = "Goal"
    if result.target is not None:
        query_label = f"Goal: EqAng({result.target[0]},{result.target[1]})"
    graph.add_node(QueryNode(id=query_id, label=query_label))

    for step in state.htrace:
        graph.add_node(SpaceNode(id=step.space, label=step.space))

    _materialize_final_entities(graph, result)

    latest_view_by_object: dict[str, tuple[str, str]] = {}
    fact_origins: Dict[str, str] = {}
    fact_spaces: Dict[str, str] = {}
    fact_derived_from: Dict[str, Set[str]] = {}

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

        for used_fact in step.used_facts:
            _add_fact_node(graph, label=used_fact, space_id=step.space, origin="seed")
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=_fact_id(used_fact), type=USES))

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
            fact_id = _fact_id(asserted)
            fact_origins[asserted] = "inference" if "congruence" in step.space or step.phase == "inference" else "construction"
            fact_spaces[asserted] = step.space
            if step.used_facts:
                fact_derived_from.setdefault(asserted, set()).update(step.used_facts)
            _add_fact_node(
                graph,
                label=asserted,
                space_id=step.space,
                origin=fact_origins[asserted],
                derived_from=fact_derived_from.get(asserted),
            )
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=ASSERTS))
            if _fact_matches_target(asserted, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for rewritten in step.rewrites:
            fact_id = _fact_id(rewritten)
            fact_origins[rewritten] = "inference"
            fact_spaces[rewritten] = step.space
            if step.used_facts:
                fact_derived_from.setdefault(rewritten, set()).update(step.used_facts)
            _add_fact_node(
                graph,
                label=rewritten,
                space_id=step.space,
                origin="inference",
                derived_from=fact_derived_from.get(rewritten),
            )
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=fact_id, type=REWRITES))
            if _fact_matches_target(rewritten, result.target):
                graph.add_edge(HPGEdge(from_id=fact_id, to_id=query_id, type=SUPPORTS_GOAL))

        for derived in step.derived_facts:
            _add_fact_node(
                graph,
                label=derived,
                space_id=step.space,
                origin="inference",
                derived_from=set(step.used_facts),
            )
            graph.add_edge(HPGEdge(from_id=projection_id, to_id=_fact_id(derived), type=DERIVES))
            if _fact_matches_target(derived, result.target):
                graph.add_edge(HPGEdge(from_id=_fact_id(derived), to_id=query_id, type=SUPPORTS_GOAL))

        for parent in step.parents:
            parent_projection_id = f"projection:{parent}"
            graph.add_node(ProjectionNode(id=parent_projection_id, label=parent))
            graph.add_edge(HPGEdge(from_id=parent_projection_id, to_id=projection_id, type=DERIVES))

    for on_ray in state.facts.on_rays:
        label = f"OnRay({on_ray.point},{on_ray.ray})"
        _add_fact_node(
            graph,
            label=label,
            space_id=fact_spaces.get(label, "fact_space"),
            origin=fact_origins.get(label, "seed"),
            derived_from=fact_derived_from.get(label),
        )
    for seg1, seg2 in state.facts.eq_segs:
        label = f"EqSeg({seg1},{seg2})"
        _add_fact_node(
            graph,
            label=label,
            space_id=fact_spaces.get(label, "fact_space"),
            origin=fact_origins.get(label, "seed"),
            derived_from=fact_derived_from.get(label),
        )
    for congruent in state.facts.congruent:
        label = f"Congruent({congruent.t1.name},{congruent.t2.name})"
        _add_fact_node(
            graph,
            label=label,
            space_id=fact_spaces.get(label, "fact_space"),
            origin=fact_origins.get(label, "inference"),
            derived_from=fact_derived_from.get(label),
        )
    for ang1, ang2 in state.facts.eq_angs:
        label = f"EqAng({ang1},{ang2})"
        _add_fact_node(
            graph,
            label=label,
            space_id=fact_spaces.get(label, "fact_space"),
            origin=fact_origins.get(label, "inference"),
            derived_from=fact_derived_from.get(label),
        )
        if _fact_matches_target(label, result.target):
            graph.add_edge(HPGEdge(from_id=_fact_id(label), to_id=query_id, type=SUPPORTS_GOAL))

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
