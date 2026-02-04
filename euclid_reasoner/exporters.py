from __future__ import annotations

from typing import Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

from .search import SearchResult


def _stringify(item: object) -> str:
    return str(item)


def _resolve_items(items: Iterable[object], lookup: Dict[str, str]) -> List[str]:
    resolved: List[str] = []
    for item in items:
        if isinstance(item, dict):
            label = item.get("label") or item.get("id") or _stringify(item)
            resolved.append(label)
            continue
        if isinstance(item, str) and item in lookup:
            resolved.append(lookup[item])
        else:
            resolved.append(_stringify(item))
    return resolved


def _main_query(hpg: dict) -> Dict[str, str]:
    if isinstance(hpg.get("query"), dict):
        return hpg["query"]
    queries = hpg.get("queries")
    if isinstance(queries, list) and queries:
        if isinstance(queries[0], dict):
            return queries[0]
    return {"id": "query:goal", "label": "Goal"}


def hpg_to_opml(hpg: dict) -> str:
    query = _main_query(hpg)
    query_label = query.get("label") or query.get("text") or "Goal"

    opml = ET.Element("opml", version="2.0")
    head = ET.SubElement(opml, "head")
    title = ET.SubElement(head, "title")
    title.text = query_label
    body = ET.SubElement(opml, "body")
    root_outline = ET.SubElement(body, "outline", text=query_label)

    projections = {proj.get("id"): proj for proj in hpg.get("projections", []) if isinstance(proj, dict)}
    run = hpg.get("run") or hpg.get("runs") or {}
    best_path = run.get("best_path_projection_ids", [])

    object_labels = {obj.get("id"): obj.get("label", obj.get("id")) for obj in hpg.get("objects", []) if isinstance(obj, dict)}
    fact_labels = {fact.get("id"): fact.get("label", fact.get("id")) for fact in hpg.get("facts", []) if isinstance(fact, dict)}

    for proj_id in best_path:
        proj = projections.get(proj_id, {"id": proj_id})
        operator = proj.get("operator", "")
        rule_ref = proj.get("rule_ref", "")
        parts = [part for part in (operator, rule_ref, proj.get("id")) if part]
        proj_text = " ".join(parts) if parts else proj_id
        proj_outline = ET.SubElement(root_outline, "outline", text=proj_text)

        creates = _resolve_items(proj.get("creates", []), object_labels)
        if creates:
            creates_outline = ET.SubElement(proj_outline, "outline", text="creates")
            for item in creates:
                ET.SubElement(creates_outline, "outline", text=item)

        asserts = _resolve_items(proj.get("asserts", []), fact_labels)
        if asserts:
            asserts_outline = ET.SubElement(proj_outline, "outline", text="asserts")
            for item in asserts:
                ET.SubElement(asserts_outline, "outline", text=item)

        if "rewrites" in proj:
            rewrites = _resolve_items(proj.get("rewrites", []), fact_labels)
            rewrites_outline = ET.SubElement(proj_outline, "outline", text="rewrites")
            for item in rewrites:
                ET.SubElement(rewrites_outline, "outline", text=item)

    return ET.tostring(opml, encoding="unicode", xml_declaration=True)


def _add_node(nodes: List[dict], node_id: str, kind: str, label: str, space: Optional[str] = None, node_type: Optional[str] = None) -> None:
    node = {"id": node_id, "kind": kind, "label": label}
    if space:
        node["space"] = space
    if node_type:
        node["type"] = node_type
    nodes.append(node)


def _add_edge(edges: List[dict], from_id: str, to_id: str, edge_type: str, label: Optional[str] = None) -> None:
    edge = {"from": from_id, "to": to_id, "type": edge_type}
    if label:
        edge["label"] = label
    edges.append(edge)


def hpg_to_graph_json(hpg: dict) -> dict:
    nodes: List[dict] = []
    edges: List[dict] = []

    spaces = hpg.get("spaces", [])
    for space in spaces:
        if isinstance(space, dict):
            _add_node(nodes, space.get("id"), "space", space.get("label") or space.get("name") or space.get("id"))

    query = _main_query(hpg)
    query_id = query.get("id", "query:goal")
    _add_node(nodes, query_id, "query", query.get("label") or query.get("text") or "Goal")

    for obj in hpg.get("objects", []):
        if not isinstance(obj, dict):
            continue
        _add_node(
            nodes,
            obj.get("id"),
            "object",
            obj.get("label") or obj.get("id"),
            space=obj.get("space"),
            node_type=obj.get("type"),
        )

    for fact in hpg.get("facts", []):
        if not isinstance(fact, dict):
            continue
        _add_node(
            nodes,
            fact.get("id"),
            "fact",
            fact.get("label") or fact.get("id"),
            space=fact.get("space"),
            node_type=fact.get("type"),
        )

    for proj in hpg.get("projections", []):
        if not isinstance(proj, dict):
            continue
        _add_node(
            nodes,
            proj.get("id"),
            "projection",
            proj.get("label") or proj.get("id"),
            space=proj.get("space"),
            node_type=proj.get("type"),
        )

        for created in proj.get("creates", []):
            created_id = created.get("id") if isinstance(created, dict) else created
            if created_id:
                _add_edge(edges, proj.get("id"), created_id, "creates")

        for asserted in proj.get("asserts", []):
            asserted_id = asserted.get("id") if isinstance(asserted, dict) else asserted
            if asserted_id:
                _add_edge(edges, proj.get("id"), asserted_id, "asserts")

        for used in proj.get("inputs", []):
            used_id = used.get("id") if isinstance(used, dict) else used
            if used_id:
                _add_edge(edges, proj.get("id"), used_id, "uses")

    for view in hpg.get("object_views", []):
        if not isinstance(view, dict):
            continue
        _add_node(
            nodes,
            view.get("id"),
            "object_view",
            view.get("label") or view.get("id"),
            space=view.get("space"),
            node_type=view.get("type"),
        )
        target = view.get("shadow_of")
        if target:
            _add_edge(edges, view.get("id"), target, "shadow_of")

    for node in nodes:
        space = node.get("space")
        if space:
            _add_edge(edges, node["id"], space, "in_space")

    goal_fact_ids: List[str] = []
    if "goal_fact_id" in query:
        goal_fact_ids.append(query["goal_fact_id"])
    goal_fact_ids.extend(query.get("goal_fact_ids", []) if isinstance(query.get("goal_fact_ids"), list) else [])

    for fact in hpg.get("facts", []):
        if not isinstance(fact, dict):
            continue
        if fact.get("id") in goal_fact_ids:
            _add_edge(edges, fact.get("id"), query_id, "supports_goal")

    return {"nodes": nodes, "edges": edges}


def result_to_hpg(result: SearchResult) -> dict:
    space_id = "space:main"
    spaces = [{"id": space_id, "label": "Main"}]

    objects = []
    for triangle in result.state.triangles:
        objects.append(
            {
                "id": f"triangle:{triangle.name}",
                "label": str(triangle),
                "space": space_id,
                "type": "triangle",
            }
        )

    facts = []
    goal_fact_id: Optional[str] = None
    eq_angs = sorted(result.state.facts.eq_angs, key=lambda pair: (str(pair[0]), str(pair[1])))
    for idx, (ang1, ang2) in enumerate(eq_angs, start=1):
        fact_id = f"fact:eqang:{idx}"
        label = f"EqAng({ang1}, {ang2})"
        facts.append({"id": fact_id, "label": label, "space": space_id, "type": "eq_ang"})
        if result.target and (ang1, ang2) == result.target:
            goal_fact_id = fact_id
        if result.target and (ang2, ang1) == result.target:
            goal_fact_id = fact_id

    if goal_fact_id is None and facts:
        goal_fact_id = facts[0]["id"]

    projection_id = "projection:sss"
    projections = [
        {
            "id": projection_id,
            "operator": "SSS",
            "rule_ref": "CongruenceSSSPrism",
            "creates": [obj["id"] for obj in objects],
            "asserts": [goal_fact_id] if goal_fact_id else [],
            "inputs": [],
            "space": space_id,
        }
    ]

    return {
        "version": "HPG-1.0",
        "spaces": spaces,
        "objects": objects,
        "facts": facts,
        "projections": projections,
        "run": {"best_path_projection_ids": [projection_id]},
        "query": {"id": "query:goal", "label": "Goal", "goal_fact_id": goal_fact_id},
    }
