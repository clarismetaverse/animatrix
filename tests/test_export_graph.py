import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.demo_prop9 import solve_prop9
from euclid_reasoner.exporters import hpg_to_graph_json, result_to_hpg


def test_export_graph_json() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)
    graph = hpg_to_graph_json(hpg)

    assert graph["nodes"]
    assert graph["edges"]

    node_types = {node["type"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}

    assert "space" in node_types
    assert "projection" in node_types
    assert "fact" in node_types
    assert "object" in node_types
    assert "view" in node_types

    assert "interprets" in edge_types
    assert "reinterprets" in edge_types or "explores" in edge_types

    interpreting_edges = [edge for edge in graph["edges"] if edge["type"] == "interprets"]
    shadow_edges = [edge for edge in graph["edges"] if edge["type"] == "shadow_of"]
    assert interpreting_edges
    assert len(shadow_edges) < len(interpreting_edges)

    fact_nodes = [node for node in graph["nodes"] if node["type"] == "fact"]
    assert any(node.get("fact_type") and node.get("space_id") for node in fact_nodes)

    projection_nodes = [node for node in graph["nodes"] if node["type"] == "projection"]
    assert any(node.get("projection_type") and node.get("space_id") for node in projection_nodes)

    if result.target is not None:
        assert "supports_goal" in edge_types
