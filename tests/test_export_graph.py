import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.core import State
from euclid_reasoner.demo_prop9 import solve_prop9
from euclid_reasoner.exporters import hpg_to_graph_json, result_to_hpg
from euclid_reasoner.types import SearchResult


def test_export_graph_json() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)
    graph = hpg_to_graph_json(hpg)

    assert graph["nodes"]
    assert graph["edges"]

    node_kinds = {node["kind"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}

    assert all("kind" in node for node in graph["nodes"])
    assert "space" in node_kinds
    assert "projection" in node_kinds
    assert "fact" in node_kinds
    assert "object" in node_kinds
    assert "view" in node_kinds

    assert "interprets" in edge_types
    assert "reinterprets" in edge_types or "explores" in edge_types
    assert "supports_goal" in edge_types

    interpreting_edges = [edge for edge in graph["edges"] if edge["type"] == "interprets"]
    shadow_edges = [edge for edge in graph["edges"] if edge["type"] == "shadow_of"]
    assert interpreting_edges
    assert not shadow_edges

    fact_nodes = [node for node in graph["nodes"] if node["kind"] == "fact"]
    assert any(node.get("fact_type") and node.get("space_id") for node in fact_nodes)

    projection_nodes = [node for node in graph["nodes"] if node["kind"] == "projection"]
    assert any(node.get("projection_type") and node.get("space_id") for node in projection_nodes)
    object_nodes = [node for node in graph["nodes"] if node["kind"] == "object"]
    assert any(node.get("object_type") for node in object_nodes)


def test_unknown_entity_creates_object_and_view_pair() -> None:
    state = State()
    state.add_step(
        prism="UnknownEntityPrism",
        label="Touch a symbolic unknown",
        space="construction_space",
        creates=["mystery:X"],
    )
    graph = result_to_hpg(SearchResult(solved=False, state=state, target=None))

    unknown_object_id = "object:mystery:X"
    unknown_view_id = "view:construction_space:mystery:X:generic"

    object_nodes = [node for node in graph["nodes"] if node["id"] == unknown_object_id]
    view_nodes = [node for node in graph["nodes"] if node["id"] == unknown_view_id]
    interpreting_edges = [
        edge
        for edge in graph["edges"]
        if edge["type"] == "interprets" and edge["from"] == unknown_view_id and edge["to"] == unknown_object_id
    ]

    assert object_nodes
    assert object_nodes[0]["kind"] == "object"
    assert object_nodes[0]["object_type"] == "unknown"
    assert view_nodes
    assert view_nodes[0]["kind"] == "view"
    assert view_nodes[0]["object_id"] == unknown_object_id
    assert interpreting_edges


def test_prop9_hpg_contains_micro_sss_and_angle_goal_support() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)

    object_nodes = [node for node in hpg["nodes"] if node["kind"] == "object"]
    fact_nodes = [node for node in hpg["nodes"] if node["kind"] == "fact"]
    supports_goal_edges = [edge for edge in hpg["edges"] if edge["type"] == "supports_goal"]

    triangle_objects = [n for n in object_nodes if n.get("object_type") == "triangle"]
    assert len(triangle_objects) >= 2

    eqseg_facts = [n for n in fact_nodes if n.get("fact_type") == "EqSeg"]
    congruent_facts = [n for n in fact_nodes if n.get("fact_type") == "Congruent"]
    eqang_facts = [n for n in fact_nodes if n.get("fact_type") == "EqAng"]

    assert len(eqseg_facts) >= 3
    assert len(congruent_facts) >= 1
    assert len(eqang_facts) >= 1

    goal_supported_by = {edge["from"] for edge in supports_goal_edges}
    assert goal_supported_by
    for fact_id in goal_supported_by:
        fact_node = next(node for node in fact_nodes if node["id"] == fact_id)
        assert fact_node["fact_type"] == "EqAng"


def test_hpg_edges_are_globally_deduplicated() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)

    edge_keys = {(edge["from"], edge["to"], edge["type"]) for edge in hpg["edges"]}
    assert len(edge_keys) == len(hpg["edges"])


def test_ray_entities_are_typed_as_rays() -> None:
    state = State()
    state.add_step(
        prism="RayEntityPrism",
        label="Touch rays directly",
        space="construction_space",
        creates=["ray:BA", "ray:BC"],
    )

    hpg = result_to_hpg(SearchResult(solved=False, state=state, target=None))

    ray_objects = [node for node in hpg["nodes"] if node["kind"] == "object" and node["id"] in {"object:ray:BA", "object:ray:BC"}]
    assert len(ray_objects) == 2
    assert {node["object_type"] for node in ray_objects} == {"ray"}


def test_goal_support_edge_is_unique_per_fact_query_pair() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)

    supports_goal_edges = [edge for edge in hpg["edges"] if edge["type"] == "supports_goal"]
    edge_pairs = {(edge["from"], edge["to"]) for edge in supports_goal_edges}

    assert len(edge_pairs) == len(supports_goal_edges)
