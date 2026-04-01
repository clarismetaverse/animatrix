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

    if result.target is not None:
        assert "supports_goal" in edge_types


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
