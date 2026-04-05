from __future__ import annotations

from typing import List

from .core import State
from .prisms import all_prisms
from .search import beam_search
from .types import SearchResult


def solve_prop10(beam_k: int = 20, steps: int = 10) -> SearchResult:
    start = State()
    return beam_search(start, prisms=all_prisms(), beam_k=beam_k, steps=steps)


def _format_facts(state: State) -> List[str]:
    lines: List[str] = []

    # OnRay facts
    for on_ray in sorted(state.facts.on_rays, key=lambda r: (r.ray, r.point)):
        lines.append(f"OnRay({on_ray.point}, {on_ray.ray})")

    # EqSeg facts (IMPORTANT for Prop. 10)
    for seg1, seg2 in sorted(state.facts.eq_segs, key=lambda pair: (str(pair[0]), str(pair[1]))):
        lines.append(f"EqSeg({seg1}, {seg2})")

    # Congruence facts
    for t in sorted(state.facts.congruent, key=lambda c: (c.t1.name, c.t2.name)):
        mapping = ",".join([f"{a}->{b}" for a, b in t.mapping])
        lines.append(f"Congruent({t.t1},{t.t2},[{mapping}])")

    return lines


def main() -> None:
    result = solve_prop10()

    print(f"Solved? {result.solved}")

    if result.target:
        print(f"Target: {result.target}")
    else:
        print("Target: None")

    print("Trace:")
    for step in result.state.trace:
        print(f"- {step}")

    print("Key facts:")
    for line in _format_facts(result.state):
        print(f"- {line}")


if __name__ == "__main__":
    main()
