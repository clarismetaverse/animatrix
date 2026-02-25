from __future__ import annotations

from typing import Iterable, Optional, Tuple

from .core import Angle, State
from .prisms import Prism
from .types import SearchResult


def goal_checker(state: State) -> Optional[Tuple[Angle, Angle]]:
    """Return a target equal-angle fact around B when discovered."""
    for ang1, ang2 in sorted(state.facts.eq_angs, key=lambda pair: (str(pair[0]), str(pair[1]))):
        if ang1.v == "B" and ang2.v == "B" and ang1.c == ang2.c:
            return (ang1, ang2)
    return None


def score(state: State) -> int:
    """Simple heuristic score for beam search ordering."""
    base = (
        len(state.facts.on_rays)
        + 2 * len(state.facts.eq_segs)
        + 3 * len(state.facts.congruent)
        + 4 * len(state.facts.eq_angs)
        + len(state.triangles)
    )
    if goal_checker(state):
        base += 1000
    return base


def _state_key(state: State) -> tuple:
    return (
        tuple(sorted((fact.point, fact.ray) for fact in state.facts.on_rays)),
        tuple(sorted((str(s1), str(s2)) for s1, s2 in state.facts.eq_segs)),
        tuple(sorted((str(a1), str(a2)) for a1, a2 in state.facts.eq_angs)),
        tuple(sorted((c.t1.name, c.t2.name, c.mapping) for c in state.facts.congruent)),
        tuple(sorted((t.name, t.vertices) for t in state.triangles)),
        state.mode,
    )


def beam_search(
    start: State,
    prisms: Iterable[Prism],
    *,
    beam_k: int = 20,
    steps: int = 10,
) -> SearchResult:
    beam = [start]
    seen = {_state_key(start)}

    initial_goal = goal_checker(start)
    if initial_goal is not None:
        return SearchResult(solved=True, state=start, target=initial_goal)

    for _ in range(steps):
        candidates: list[State] = []
        for state in beam:
            for prism in prisms:
                for applied in prism.apply(state):
                    new_state = applied.state
                    key = _state_key(new_state)
                    if key in seen:
                        continue
                    seen.add(key)

                    target = goal_checker(new_state)
                    if target is not None:
                        return SearchResult(solved=True, state=new_state, target=target)

                    candidates.append(new_state)

        if not candidates:
            break

        candidates.sort(key=score, reverse=True)
        beam = candidates[:beam_k]

    best = max(beam, key=score) if beam else start
    return SearchResult(solved=False, state=best, target=goal_checker(best))
