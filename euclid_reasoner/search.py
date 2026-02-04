from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .core import Angle, State
from .prisms import Prism, all_prisms


@dataclass(frozen=True)
class SearchResult:
    solved: bool
    state: State
    target: Optional[Tuple[Angle, Angle]]


def goal_checker(state: State) -> Optional[Tuple[Angle, Angle]]:
    for ang1, ang2 in state.facts.eq_angs:
        if ang1.v == "B" and ang2.v == "B" and ang1.c == ang2.c:
            return (ang1, ang2)
    return None


def score(state: State) -> int:
    value = 0
    if goal_checker(state):
        value += 1000
    value += 50 * len(state.facts.congruent)
    value += 5 * len(state.facts.eq_angs)
    value += 2 * len(state.facts.eq_segs)
    value += len(state.facts.on_rays)
    return value


def beam_search(
    start: State,
    prisms: Optional[List[Prism]] = None,
    beam_k: int = 20,
    steps: int = 10,
) -> SearchResult:
    prisms = prisms or all_prisms()
    beam: List[State] = [start]
    best_goal: Optional[Tuple[Angle, Angle]] = None
    for _ in range(steps):
        candidates: List[State] = []
        for state in beam:
            goal = goal_checker(state)
            if goal:
                return SearchResult(True, state, goal)
            for prism in prisms:
                for result in prism.apply(state):
                    candidates.append(result.state)
        if not candidates:
            break
        candidates.sort(key=score, reverse=True)
        beam = candidates[:beam_k]
        best_goal = goal_checker(beam[0])
        if best_goal:
            return SearchResult(True, beam[0], best_goal)
    return SearchResult(False, beam[0], best_goal)
