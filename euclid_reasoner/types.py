from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .core import Angle, State


@dataclass(frozen=True)
class SearchResult:
    solved: bool
    state: State
    target: Optional[Tuple[Angle, Angle]]
