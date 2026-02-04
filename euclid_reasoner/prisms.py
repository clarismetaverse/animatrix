from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .core import (
    Congruent,
    Segment,
    State,
    Triangle,
    derive_angles_from_congruence,
    match_sss,
)


@dataclass(frozen=True)
class PrismResult:
    state: State
    description: str


class Prism:
    name: str = ""

    def apply(self, state: State) -> List[PrismResult]:
        raise NotImplementedError


class ChoosePointOnRayBA(Prism):
    name = "ChoosePointOnRayBA"

    def apply(self, state: State) -> List[PrismResult]:
        if state.facts.all_points_on_ray("BA"):
            return []
        results: List[PrismResult] = []
        for idx in range(1, 5):
            new_state = state.copy()
            point = f"D{idx}"
            if new_state.facts.add_on_ray(point, "BA"):
                new_state.add_trace(f"Choose {point} on ray BA")
                results.append(PrismResult(new_state, f"Choose {point} on ray BA"))
        return results


class CopyLengthToRayBC(Prism):
    name = "CopyLengthToRayBC"

    def apply(self, state: State) -> List[PrismResult]:
        results: List[PrismResult] = []
        for point in state.facts.all_points_on_ray("BA"):
            new_state = state.copy()
            target = f"E_{point}"
            seg_bd = Segment("B", point)
            seg_be = Segment("B", target)
            changed = new_state.facts.add_on_ray(target, "BC")
            changed = new_state.facts.add_eqseg(seg_bd, seg_be) or changed
            if changed:
                new_state.add_trace(
                    f"Copy {seg_bd} to ray BC -> {target} with BE=BD"
                )
                results.append(
                    PrismResult(
                        new_state,
                        f"Copy {seg_bd} to ray BC -> {target} with BE=BD",
                    )
                )
        return results


class EquilateralOnSegment(Prism):
    name = "EquilateralOnSegment"

    def apply(self, state: State) -> List[PrismResult]:
        results: List[PrismResult] = []
        points_d = state.facts.all_points_on_ray("BA")
        points_e = state.facts.all_points_on_ray("BC")
        for d in points_d:
            for e in points_e:
                apex = f"F_{d}_{e}"
                new_state = state.copy()
                seg_df = Segment(d, apex)
                seg_ef = Segment(e, apex)
                if new_state.facts.add_eqseg(seg_df, seg_ef):
                    new_state.mode = "EquilateralField"
                    new_state.add_trace(
                        f"Construct equilateral on {d}{e} -> apex {apex}"
                    )
                    results.append(
                        PrismResult(
                            new_state,
                            f"Construct equilateral on {d}{e} -> apex {apex}",
                        )
                    )
        return results


class InstantiateComparisonTriangles(Prism):
    name = "InstantiateComparisonTriangles"

    def apply(self, state: State) -> List[PrismResult]:
        results: List[PrismResult] = []
        points_d = state.facts.all_points_on_ray("BA")
        points_e = state.facts.all_points_on_ray("BC")
        for d in points_d:
            for e in points_e:
                apex = f"F_{d}_{e}"
                t1 = Triangle(f"T_{d}{apex}B", (d, apex, "B"))
                t2 = Triangle(f"T_{e}{apex}B", (e, apex, "B"))
                if t1 in state.triangles and t2 in state.triangles:
                    continue
                new_state = state.copy()
                new_state.triangles.extend([t1, t2])
                new_state.facts.add_eqseg(Segment("B", apex), Segment("B", apex))
                new_state.add_trace(
                    f"Instantiate triangles {t1} and {t2} with common BF"
                )
                results.append(
                    PrismResult(
                        new_state,
                        f"Instantiate triangles {t1} and {t2} with common BF",
                    )
                )
        return results


class CongruenceSSSPrism(Prism):
    name = "CongruenceSSSPrism"

    def apply(self, state: State) -> List[PrismResult]:
        results: List[PrismResult] = []
        tris = state.triangles
        for i in range(len(tris)):
            for j in range(i + 1, len(tris)):
                t1, t2 = tris[i], tris[j]
                mapping = match_sss(state.facts, t1, t2)
                if mapping is None:
                    continue
                new_state = state.copy()
                congruent = Congruent(t1, t2, mapping)
                if not new_state.facts.add_congruent(congruent):
                    continue
                new_state.mode = "CongruenceField"
                for ang1, ang2 in derive_angles_from_congruence(t1.vertices, mapping):
                    new_state.facts.add_eqang(ang1, ang2)
                new_state.add_trace(
                    f"SSS congruence found between {t1} and {t2}"
                )
                results.append(
                    PrismResult(
                        new_state,
                        f"SSS congruence found between {t1} and {t2}",
                    )
                )
        return results


def all_prisms() -> List[Prism]:
    return [
        ChoosePointOnRayBA(),
        CopyLengthToRayBC(),
        EquilateralOnSegment(),
        InstantiateComparisonTriangles(),
        CongruenceSSSPrism(),
    ]
