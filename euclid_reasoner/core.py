from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple


@dataclass(frozen=True, order=True)
class Segment:
    p: str
    q: str

    def __post_init__(self) -> None:
        if self.p > self.q:
            p, q = self.q, self.p
            object.__setattr__(self, "p", p)
            object.__setattr__(self, "q", q)

    def __str__(self) -> str:
        return f"{self.p}{self.q}"


@dataclass(frozen=True)
class Angle:
    a: str
    v: str
    c: str

    def __str__(self) -> str:
        return f"∠{self.a}{self.v}{self.c}"


@dataclass(frozen=True)
class Triangle:
    name: str
    vertices: Tuple[str, str, str]

    def __str__(self) -> str:
        return f"{self.name}({''.join(self.vertices)})"


@dataclass(frozen=True)
class OnRay:
    point: str
    ray: str


@dataclass(frozen=True)
class EqSeg:
    seg1: Segment
    seg2: Segment


@dataclass(frozen=True)
class EqAng:
    ang1: Angle
    ang2: Angle


@dataclass(frozen=True)
class Congruent:
    t1: Triangle
    t2: Triangle
    mapping: Tuple[Tuple[str, str], ...]


@dataclass
class Facts:
    on_rays: Set[OnRay] = field(default_factory=set)
    eq_segs: Set[Tuple[Segment, Segment]] = field(default_factory=set)
    eq_angs: Set[Tuple[Angle, Angle]] = field(default_factory=set)
    congruent: Set[Congruent] = field(default_factory=set)

    def add_on_ray(self, point: str, ray: str) -> bool:
        fact = OnRay(point, ray)
        if fact in self.on_rays:
            return False
        self.on_rays.add(fact)
        return True

    def add_eqseg(self, seg1: Segment, seg2: Segment) -> bool:
        pair = tuple(sorted((seg1, seg2), key=str))
        if pair in self.eq_segs:
            return False
        self.eq_segs.add(pair)
        return True

    def add_eqang(self, ang1: Angle, ang2: Angle) -> bool:
        pair = tuple(sorted((ang1, ang2), key=str))
        if pair in self.eq_angs:
            return False
        self.eq_angs.add(pair)
        return True

    def add_congruent(self, congruent: Congruent) -> bool:
        if congruent in self.congruent:
            return False
        self.congruent.add(congruent)
        return True

    def has_eqseg(self, seg1: Segment, seg2: Segment) -> bool:
        pair = tuple(sorted((seg1, seg2), key=str))
        return pair in self.eq_segs

    def all_points_on_ray(self, ray: str) -> List[str]:
        return [fact.point for fact in sorted(self.on_rays, key=lambda r: r.point) if fact.ray == ray]

    def eqang_with_vertex(self, vertex: str) -> List[Tuple[Angle, Angle]]:
        return [pair for pair in self.eq_angs if pair[0].v == vertex or pair[1].v == vertex]


@dataclass
class State:
    facts: Facts = field(default_factory=Facts)
    triangles: List[Triangle] = field(default_factory=list)
    mode: str = "Seed"
    trace: List[str] = field(default_factory=list)

    def copy(self) -> "State":
        return State(
            facts=Facts(
                on_rays=set(self.facts.on_rays),
                eq_segs=set(self.facts.eq_segs),
                eq_angs=set(self.facts.eq_angs),
                congruent=set(self.facts.congruent),
            ),
            triangles=list(self.triangles),
            mode=self.mode,
            trace=list(self.trace),
        )

    def add_trace(self, message: str) -> None:
        self.trace.append(message)


def angle_at(vertex: str, left: str, right: str) -> Angle:
    return Angle(left, vertex, right)


def triangle_sides(vertices: Tuple[str, str, str]) -> Tuple[Segment, Segment, Segment]:
    a, b, c = vertices
    return (Segment(a, b), Segment(b, c), Segment(c, a))


def triangle_angles(vertices: Tuple[str, str, str]) -> Tuple[Angle, Angle, Angle]:
    a, b, c = vertices
    return (Angle(b, a, c), Angle(a, b, c), Angle(a, c, b))


def match_sss(facts: Facts, t1: Triangle, t2: Triangle) -> Optional[Tuple[Tuple[str, str], ...]]:
    v1 = t1.vertices
    v2 = t2.vertices
    permutations = [
        (v2[0], v2[1], v2[2]),
        (v2[0], v2[2], v2[1]),
        (v2[1], v2[0], v2[2]),
        (v2[1], v2[2], v2[0]),
        (v2[2], v2[0], v2[1]),
        (v2[2], v2[1], v2[0]),
    ]
    sides1 = triangle_sides(v1)
    for perm in permutations:
        sides2 = triangle_sides(perm)
        if all(facts.has_eqseg(s1, s2) for s1, s2 in zip(sides1, sides2)):
            return tuple(zip(v1, perm))
    return None


def derive_angles_from_congruence(
    t1_vertices: Tuple[str, str, str], mapping: Tuple[Tuple[str, str], ...]
) -> List[Tuple[Angle, Angle]]:
    map_dict = {a: b for a, b in mapping}
    v2 = tuple(map_dict[v] for v in t1_vertices)
    angles1 = triangle_angles(t1_vertices)
    angles2 = triangle_angles(v2)
    return list(zip(angles1, angles2))
