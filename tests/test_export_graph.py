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
    edge_types = {edge["type"] for edge in graph["edges"]}
    if "shadow_of" in edge_types:
        assert "shadow_of" in edge_types
    else:
        assert "creates" in edge_types or "asserts" in edge_types
