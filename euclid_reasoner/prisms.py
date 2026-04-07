from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .core import (
    Congruent,
    Segment,
    State,
    Triangle,
    TriangleCorrespondence,
    triangle_sides,
    derive_angles_from_correspondence,
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


# -------------------------------------------------------------

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
                label = f"Choose {point} on ray BA"

                new_state.add_step(
                    prism=self.name,
                    label=label,
                    space="construction_space",
                    uses=["ray:BA"],
                    creates=[f"point:{point}"],
                    asserts=[f"OnRay({point},BA)"],
                    used_facts=[],
                    created_objects=[f"point:{point}"],
                    derived_facts=[],
                    phase="construction",
                    granularity="micro",
                )

                results.append(PrismResult(new_state, label))
        return results


# -------------------------------------------------------------

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
                label = f"Copy {seg_bd} to ray BC -> {target} with BE=BD"

                new_state.add_step(
                    prism=self.name,
                    label=label,
                    space="construction_space",
                    uses=[f"point:{point}", f"segment:{seg_bd}", "ray:BC"],
                    creates=[f"point:{target}"],
                    asserts=[
                        f"OnRay({target},BC)",
                        f"EqSeg({seg_bd},{seg_be})",
                    ],
                    used_facts=[f"OnRay({point},BA)"],
                    created_objects=[f"point:{target}", f"segment:{seg_be}"],
                    derived_facts=[],
                    phase="construction",
                    granularity="micro",
                )

                results.append(PrismResult(new_state, label))
        return results


# -------------------------------------------------------------

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
                tri = Triangle(f"T_eq_{d}{e}{apex}", (d, e, apex))

                if new_state.facts.add_eqseg(seg_df, seg_ef):
                    new_state.mode = "EquilateralField"
                    if tri not in new_state.triangles:
                        new_state.triangles.append(tri)
                    label = f"Construct equilateral on {d}{e} -> apex {apex}"

                    new_state.add_step(
                        prism=self.name,
                        label=label,
                        space="equilateral_space",
                        uses=[f"point:{d}", f"point:{e}", f"segment:{Segment(d, e)}"],
                        creates=[f"point:{apex}", f"triangle:{tri.name}"],
                        asserts=[f"EqSeg({seg_df},{seg_ef})"],
                        used_facts=[f"OnRay({d},BA)", f"OnRay({e},BC)"],
                        created_objects=[
                            f"point:{apex}",
                            f"segment:{seg_df}",
                            f"segment:{seg_ef}",
                            f"triangle:{tri.name}",
                        ],
                        derived_facts=[],
                        phase="construction",
                        granularity="micro",
                    )

                    results.append(PrismResult(new_state, label))
        return results


# -------------------------------------------------------------

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

                label = f"Instantiate triangles {t1} and {t2} with common BF"

                new_state.add_step(
                    prism=self.name,
                    label=label,
                    space="triangle_space",
                    uses=[
                        f"point:{d}",
                        f"point:{e}",
                        f"point:{apex}",
                        f"segment:{Segment('B', d)}",
                        f"segment:{Segment('B', e)}",
                        f"segment:{Segment('B', apex)}",
                    ],
                    creates=[f"triangle:{t1.name}", f"triangle:{t2.name}"],
                    asserts=[f"EqSeg(B{apex},B{apex})"],
                    used_facts=[
                        f"OnRay({d},BA)",
                        f"OnRay({e},BC)",
                    ],
                    created_objects=[f"triangle:{t1.name}", f"triangle:{t2.name}"],
                    derived_facts=[],
                    phase="triangle_instantiation",
                    granularity="micro",
                )

                results.append(PrismResult(new_state, label))
        return results


# -------------------------------------------------------------

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

                corr = TriangleCorrespondence(t1, t2, mapping)
                new_state.facts.add_correspondence(corr)

                new_state.mode = "CongruenceField"

                derived = derive_angles_from_correspondence(corr)
                sides1 = triangle_sides(t1.vertices)
                sides2 = triangle_sides(tuple(b for _, b in mapping))
                sss_equalities = [f"EqSeg({s1},{s2})" for s1, s2 in zip(sides1, sides2)]
                for ang1, ang2 in derived:
                    new_state.facts.add_eqang(ang1, ang2)

                label = f"SSS congruence found between {t1} and {t2}"

                new_state.add_step(
                    prism=self.name,
                    label=label,
                    space="congruence_space",
                    uses=[
                        f"triangle:{t1.name}",
                        f"triangle:{t2.name}",
                        *[f"segment:{s}" for s in sides1],
                        *[f"segment:{s}" for s in sides2],
                    ],
                    creates=[],
                    asserts=[f"Congruent({t1.name},{t2.name})", str(corr)],
                    rewrites=[f"EqAng({a1},{a2})" for (a1, a2) in derived],
                    used_facts=sss_equalities,
                    created_objects=[],
                    derived_facts=[f"EqAng({a1},{a2})" for (a1, a2) in derived],
                    phase="inference",
                    granularity="micro",
                )

                results.append(PrismResult(new_state, label))

        return results


# -------------------------------------------------------------

def all_prisms() -> List[Prism]:
    return [
        ChoosePointOnRayBA(),
        CopyLengthToRayBC(),
        EquilateralOnSegment(),
        InstantiateComparisonTriangles(),
        CongruenceSSSPrism(),
    ]
