"""Mini Euclid Reasoner package."""

from .core import (
    Angle,
    Congruent,
    EqAng,
    EqSeg,
    Facts,
    OnRay,
    Segment,
    State,
    Triangle,
)
from .demo_prop9 import solve_prop9

__all__ = [
    "Angle",
    "Congruent",
    "EqAng",
    "EqSeg",
    "Facts",
    "OnRay",
    "Segment",
    "State",
    "Triangle",
    "solve_prop9",
]
