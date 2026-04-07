from __future__ import annotations

from typing import List, Optional, Tuple

from .core import Segment, State
from .prisms import all_prisms
from .search import beam_search
from .types import SearchResult


def solve_prop10(beam_k: int = 20, steps: int = 10) -> SearchResult:
    start = State()
    return beam_search(start, prisms=all_prisms(), beam_k=beam_k, steps=steps)


def find_prop10_goal(state: State) -> Optional[Tuple[Segment, Segment]]:
    """
    Find a midpoint-like structure:
    - seg1 == seg2
    - they share exactly one endpoint (candidate midpoint)
    - the other endpoints lie on the same ray
      (so the two equal segments can be read as two local views
       of a single parent segment being cut)
    """

    point_to_ray = {}
    for fact in state.facts.on_rays:
        point_to_ray[fact.point] = fact.ray

    for seg1, seg2 in sorted(state.facts.eq_segs, key=lambda pair: (str(pair[0]), str(pair[1]))):
        pts1 = {seg1.p, seg1.q}
        pts2 = {seg2.p, seg2.q}

        common = pts1 & pts2
        if len(common) != 1:
            continue

        other1 = (pts1 - common).pop()
        other2 = (pts2 - common).pop()

        if other1 == other2:
            continue

        ray1 = point_to_ray.get(other1)
        ray2 = point_to_ray.get(other2)

        if ray1 is not None and ray1 == ray2:
            return seg1, seg2

    return None


def _format_facts(state: State) -> List[str]:
    lines: List[str] = []

    for on_ray in sorted(state.facts.on_rays, key=lambda r: (r.ray, r.point)):
        lines.append(f"OnRay({on_ray.point}, {on_ray.ray})")

    for seg1, seg2 in sorted(state.facts.eq_segs, key=lambda pair: (str(pair[0]), str(pair[1]))):
        lines.append(f"EqSeg({seg1}, {seg2})")

    for t in sorted(state.facts.congruent, key=lambda c: (c.t1.name, c.t2.name)):
        mapping = ",".join([f"{a}->{b}" for a, b in t.mapping])
        lines.append(f"Congruent({t.t1},{t.t2},[{mapping}])")
    for corr in sorted(state.facts.correspondences, key=lambda c: (c.t1.name, c.t2.name)):
        mapping = ",".join([f"{a}->{b}" for a, b in corr.mapping])
        lines.append(f"Correspondence({corr.t1},{corr.t2},[{mapping}])")

    return lines


def main() -> None:
    result = solve_prop10()
    prop10_goal = find_prop10_goal(result.state)

    print(f"Solved by beam search? {result.solved}")

    if result.target:
        print(f"Native target: {result.target}")
    else:
        print("Native target: None")

    if prop10_goal:
        seg1, seg2 = prop10_goal
        print(f"Prop10-style goal found: EqSeg({seg1}, {seg2})")
    else:
        print("Prop10-style goal found: None")

    print("Trace:")
    for step in result.state.trace:
        print(f"- {step}")

    print("Key facts:")
    for line in _format_facts(result.state):
        print(f"- {line}")


if __name__ == "__main__":
    main()
