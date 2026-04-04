from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class TraceStep:
    id: str
    prism: str
    label: str
    space: str
    uses: List[str] = field(default_factory=list)
    creates: List[str] = field(default_factory=list)
    asserts: List[str] = field(default_factory=list)
    rewrites: List[str] = field(default_factory=list)
    used_facts: List[str] = field(default_factory=list)
    created_objects: List[str] = field(default_factory=list)
    derived_facts: List[str] = field(default_factory=list)
    phase: str = ""
    granularity: str = "macro"
    parents: List[str] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
