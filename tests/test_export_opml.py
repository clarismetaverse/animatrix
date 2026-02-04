import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.demo_prop9 import solve_prop9
from euclid_reasoner.exporters import hpg_to_opml, result_to_hpg


def test_export_opml() -> None:
    result = solve_prop9()
    hpg = result_to_hpg(result)
    opml = hpg_to_opml(hpg)
    assert "<opml" in opml
    assert "Goal" in opml
    assert "SSS" in opml
