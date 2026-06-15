from __future__ import annotations

from collections import Counter
from typing import Iterable, Tuple

from .demo_prop9 import solve_prop9
from .trace_schema import TraceStep


Transition = Tuple[str, str, str]


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



def main() -> None:
    result = solve_prop9()
    transitions = extract_space_transitions(result.state.htrace)

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
