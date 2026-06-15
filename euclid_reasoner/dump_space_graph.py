from __future__ import annotations

import sys
from collections import Counter
from typing import Callable, Iterable, Tuple

from .demo_prop5 import solve_prop5
from .demo_prop9 import solve_prop9
from .demo_prop10 import solve_prop10
from .trace_schema import TraceStep
from .types import SearchResult


Transition = Tuple[str, str, str]
Solver = Callable[[], SearchResult]


SOLVERS: dict[str, Solver] = {
    "prop5": solve_prop5,
    "prop9": solve_prop9,
    "prop10": solve_prop10,
}


def _space_transition(step: TraceStep) -> Transition | None:
    source = step.meta.get("source_space")
    target = step.meta.get("target_space") or step.space
    movement = step.meta.get("movement") or step.phase or step.prism

    if not source or not target:
        return None

    return (source, target, movement)


def extract_space_transitions(htrace: Iterable[TraceStep]) -> list[Transition]:
    transitions: list[Transition] = []
    for step in htrace:
        transition = _space_transition(step)
        if transition is not None:
            transitions.append(transition)
    return transitions


def print_space_graph(transitions: Iterable[Transition]) -> None:
    counts = Counter(transitions)

    print("Mental Space Graph")
    print("==================")

    if not counts:
        print("No mental-space transitions found in htrace.")
        return

    for (source, target, movement), count in sorted(counts.items()):
        suffix = f" x{count}" if count > 1 else ""
        print(f"{source} --[{movement}]--> {target}{suffix}")


def print_space_path(transitions: Iterable[Transition]) -> None:
    transitions = list(transitions)

    print()
    print("Mental Space Path")
    print("=================")

    if not transitions:
        print("No mental-space path found.")
        return

    first_source, _, _ = transitions[0]
    print(first_source)
    for _, target, movement in transitions:
        print(f"  --[{movement}]--> {target}")


def _select_solver(argv: list[str]) -> tuple[str, Solver]:
    if len(argv) < 2:
        return "prop9", solve_prop9

    name = argv[1].lower().strip()
    if name not in SOLVERS:
        valid = ", ".join(sorted(SOLVERS))
        raise SystemExit(f"Unknown proposition '{name}'. Valid options: {valid}")

    return name, SOLVERS[name]


def main() -> None:
    prop_name, solver = _select_solver(sys.argv)
    result = solver()
    transitions = extract_space_transitions(result.state.htrace)

    print(f"Proposition: {prop_name}")
    print(f"Solved? {result.solved}")
    if result.target:
        print(f"Target equality: {result.target}")
    else:
        print("Target equality: None")
    print()

    print_space_graph(transitions)
    print_space_path(transitions)


if __name__ == "__main__":
    main()
