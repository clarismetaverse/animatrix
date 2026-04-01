import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.hpg_model import build_minimal_example_hpg


def test_build_minimal_example_hpg() -> None:
    graph = build_minimal_example_hpg().to_dict()
    node_types = {node["type"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}
    fact_nodes = [node for node in graph["nodes"] if node["type"] == "fact"]
    projection_nodes = [node for node in graph["nodes"] if node["type"] == "projection"]
    object_nodes = [node for node in graph["nodes"] if node["type"] == "object"]
    view_nodes = [node for node in graph["nodes"] if node["type"] == "view"]

    assert {"space", "object", "view", "projection", "fact", "query"}.issubset(node_types)
    assert {"in_space", "interprets", "creates", "asserts", "supports_goal"}.issubset(edge_types)
    assert "shadow_of" not in edge_types
    assert fact_nodes and fact_nodes[0].get("fact_type") and fact_nodes[0].get("space_id")
    assert projection_nodes and projection_nodes[0].get("projection_type") and projection_nodes[0].get("space_id")
    assert object_nodes and object_nodes[0].get("object_type")
    assert view_nodes and view_nodes[0].get("role") and view_nodes[0].get("object_id") and view_nodes[0].get("space_id")
