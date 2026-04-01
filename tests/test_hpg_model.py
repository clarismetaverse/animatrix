import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.hpg_model import build_minimal_example_hpg


def test_build_minimal_example_hpg() -> None:
    graph = build_minimal_example_hpg().to_dict()
    node_types = {node["type"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}

    assert {"space", "object", "view", "projection", "fact", "query"}.issubset(node_types)
    assert {"in_space", "interprets", "creates", "asserts", "supports_goal"}.issubset(edge_types)
