import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from euclid_reasoner.demo_prop9 import solve_prop9


def test_prop9_solution() -> None:
    result = solve_prop9()
    assert result.solved is True
    assert result.target is not None
    ang1, ang2 = result.target
    assert ang1.v == "B" and ang2.v == "B"
    assert ang1.c == ang2.c
