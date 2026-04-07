from __future__ import annotations

from typing import Callable, Iterable, Optional, Tuple

from .core import Angle, State
from .prisms import Prism
from .types import SearchResult


def goal_checker_prop9(state: State) -> Optional[Tuple[Angle, Angle]]:
    for ang1, ang2 in state.facts.eq_angs:
        if ang1.v == "B" and ang2.v == "B" and ang1.c == ang2.c:
            return (ang1, ang2)
    return None


def goal_checker_prop5(state: State) -> Optional[Tuple[Angle, Angle]]:

GoalFn = Callable[[State], Optional[Tuple[Angle, Angle]]]


def score(state: State, goal_fn: GoalFn = goal_checker_prop9) -> int:
    base = (
        len(state.facts.on_rays)
        + 2 * len(state.facts.eq_segs)
        + 3 * len(state.facts.congruent)
        + 4 * len(state.facts.eq_angs)
        + len(state.triangles)
    )
    if goal_fn(state):
        base += 1000
    return base


def beam_search(
    start: State,
    prisms: Iterable[Prism],
    *,
    beam_k: int = 20,
    steps: int = 10,
    goal_fn: GoalFn = goal_checker_prop9,
) -> SearchResult:
    beam = [start]

    initial_goal = goal_fn(start)
    if initial_goal:
        return SearchResult(True, start, initial_goal)

    for _ in range(steps):
        candidates = []

        for state in beam:
            for prism in prisms:
                for res in prism.apply(state):
                    new_state = res.state

                    goal = goal_fn(new_state)
                    if goal:
                        return SearchResult(True, new_state, goal)

                    candidates.append(new_state)

        if not candidates:
            break

        candidates.sort(key=lambda s: score(s, goal_fn=goal_fn), reverse=True)
        beam = candidates[:beam_k]

    best = max(beam, key=lambda s: score(s, goal_fn=goal_fn)) if beam else start
    return SearchResult(False, best, goal_fn(best))
