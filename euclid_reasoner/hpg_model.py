from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

IN_SPACE = "in_space"
INTERPRETS = "interprets"
USES = "uses"
CREATES = "creates"
ASSERTS = "asserts"
REWRITES = "rewrites"
DERIVES = "derives"
SUPPORTS_GOAL = "supports_goal"
SHADOW_OF = "shadow_of"
REINTERPRETS = "reinterprets"
EXPLORES = "explores"


@dataclass(frozen=True)
class HPGNode:
    id: str
    label: str
    type: str
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SpaceNode(HPGNode):
    pass


@dataclass(frozen=True)
class ObjectNode(HPGNode):
    object_type: str = ""


@dataclass(frozen=True)
class ViewNode(HPGNode):
    role: str = ""
    object_id: str = ""
    space_id: str = ""


@dataclass(frozen=True)
class ProjectionNode(HPGNode):
    projection_type: str = ""
    space_id: str = ""


@dataclass(frozen=True)
class FactNode(HPGNode):
    fact_type: str = ""
    space_id: str = ""


@dataclass(frozen=True)
class QueryNode(HPGNode):
    pass


@dataclass(frozen=True)
class HPGEdge:
    from_id: str
    to_id: str
    type: str
    meta: Dict[str, str] = field(default_factory=dict)


@dataclass
class HPGGraph:
    nodes: List[HPGNode] = field(default_factory=list)
    edges: List[HPGEdge] = field(default_factory=list)
    _node_ids: set[str] = field(default_factory=set, init=False, repr=False)

    def add_node(self, node: HPGNode) -> None:
        if node.id in self._node_ids:
            return
        self._node_ids.add(node.id)
        self.nodes.append(node)

    def add_edge(self, edge: HPGEdge) -> None:
        self.edges.append(edge)

    def to_dict(self) -> dict:
        return {
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [
                {"from": edge.from_id, "to": edge.to_id, "type": edge.type, "meta": edge.meta}
                for edge in self.edges
            ],
        }


def build_minimal_example_hpg() -> HPGGraph:
    graph = HPGGraph()

    space = SpaceNode(id="space:construction", label="construction", type="space")
    obj = ObjectNode(id="object:segment:AB", label="segment:AB", type="object", object_type="segment")
    view = ViewNode(
        id="view:construction:segment:AB:generic",
        label="segment:AB@generic",
        type="view",
        role="generic",
        object_id=obj.id,
        space_id=space.id,
    )
    proj = ProjectionNode(
        id="projection:hstep:0",
        label="Construct AB",
        type="projection",
        projection_type="Construct",
        space_id=space.id,
    )
    fact = FactNode(
        id="fact:EqSeg(AB,AB)",
        label="EqSeg(AB,AB)",
        type="fact",
        fact_type="EqSeg",
        space_id=space.id,
    )
    query = QueryNode(id="query:goal", label="Goal", type="query")

    for node in (space, obj, view, proj, fact, query):
        graph.add_node(node)

    graph.add_edge(HPGEdge(from_id=proj.id, to_id=space.id, type=IN_SPACE))
    graph.add_edge(HPGEdge(from_id=proj.id, to_id=view.id, type=CREATES))
    graph.add_edge(HPGEdge(from_id=view.id, to_id=obj.id, type=INTERPRETS))
    graph.add_edge(HPGEdge(from_id=proj.id, to_id=fact.id, type=ASSERTS))
    graph.add_edge(HPGEdge(from_id=fact.id, to_id=query.id, type=SUPPORTS_GOAL))

    return graph
