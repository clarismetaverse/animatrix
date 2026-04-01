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

    if result.target is not None:
        assert "supports_goal" in edge_types
