import dagre from 'dagre';
import { Edge, MarkerType, Node } from 'reactflow';
import { EdgeVisibility, HPGEdge, HPGGraph, HPGNode, KindVisibility } from '../types';

const kindStyles: Record<string, { background: string; border: string }> = {
  space: { background: '#ede9fe', border: '#7c3aed' },
  object: { background: '#dbeafe', border: '#2563eb' },
  view: { background: '#cffafe', border: '#0891b2' },
  projection: { background: '#ffedd5', border: '#ea580c' },
  fact: { background: '#dcfce7', border: '#16a34a' },
  query: { background: '#fee2e2', border: '#dc2626' },
};

const edgeStyleMap: Record<string, Partial<Edge>> = {
  interprets: { style: { strokeWidth: 1.5 } },
  uses: { style: { strokeDasharray: '6 4' } },
  creates: { style: { strokeWidth: 2.8 } },
  asserts: { style: { stroke: '#16a34a', strokeWidth: 2.2 } },
  rewrites: { style: { strokeDasharray: '2 6' } },
  derives: { style: { stroke: '#111827', strokeWidth: 2 } },
  supports_goal: { style: { stroke: '#f59e0b', strokeWidth: 3 } },
  reinterprets: { type: 'smoothstep', style: { strokeDasharray: '5 5' } },
  explores: { style: { stroke: '#94a3b8', strokeDasharray: '8 4' } },
  in_space: { style: { stroke: '#cbd5e1', strokeWidth: 1 } },
};

export const KNOWN_NODE_KINDS = ['space', 'object', 'view', 'projection', 'fact', 'query'];
const PROOF_STEP_ID = /^projection:hstep:(\d+)$/;

export interface TimelineStep {
  step: number;
  nodeId: string;
  label: string;
}

interface StepFilterResult {
  graph: HPGGraph;
  newNodeIds: Set<string>;
  newEdgeIds: Set<string>;
}

export const getDefaultKindVisibility = (nodes: HPGNode[]): KindVisibility =>
  nodes.reduce<KindVisibility>((acc, node) => {
    acc[node.kind] = true;
    return acc;
  }, {});

export const getDefaultEdgeVisibility = (edges: HPGEdge[]): EdgeVisibility =>
  edges.reduce<EdgeVisibility>((acc, edge) => {
    acc[edge.type] = true;
    return acc;
  }, {});

const nodeToFlowNode = (node: HPGNode, highlighted: boolean): Node => {
  const palette = kindStyles[node.kind] ?? { background: '#f8fafc', border: '#475569' };
  return {
    id: node.id,
    data: { label: node.label },
    position: { x: 0, y: 0 },
    type: 'default',
    style: {
      borderRadius: node.kind === 'space' ? 14 : 8,
      border: `2px solid ${palette.border}`,
      background: palette.background,
      minWidth: 150,
      fontSize: 12,
      boxShadow: highlighted ? '0 0 0 3px rgba(245,158,11,0.45)' : undefined,
    },
  };
};

const edgeToFlowEdge = (edge: HPGEdge, highlighted: boolean): Edge => {
  const base = edgeStyleMap[edge.type] ?? {};
  const style = {
    stroke: '#334155',
    strokeWidth: 1.6,
    ...(base.style ?? {}),
    ...(highlighted ? { stroke: '#f59e0b', strokeWidth: 3.2 } : {}),
  };

  return {
    id: `${edge.from}-${edge.to}-${edge.type}`,
    source: edge.from,
    target: edge.to,
    label: edge.type,
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: style.stroke },
    animated: highlighted,
    ...base,
    style,
  };
};

const getEdgeKey = (edge: HPGEdge) => `${edge.from}-${edge.to}-${edge.type}`;

const getVisibleNodeIdsUpToStep = (graph: HPGGraph, step: number): Set<string> => {
  const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
  const projectionIds = new Set(
    graph.nodes
      .filter((node) => {
        const match = PROOF_STEP_ID.exec(node.id);
        return node.kind === 'projection' && match && Number(match[1]) <= step;
      })
      .map((node) => node.id),
  );

  const visible = new Set(projectionIds);

  graph.edges.forEach((edge) => {
    if (projectionIds.has(edge.from) || projectionIds.has(edge.to)) {
      visible.add(edge.from);
      visible.add(edge.to);
    }
  });

  graph.edges.forEach((edge) => {
    const from = nodeById.get(edge.from);
    const to = nodeById.get(edge.to);
    if (!from || !to) return;
    if (visible.has(edge.from) && (to.kind === 'space' || to.kind === 'query')) visible.add(edge.to);
    if (visible.has(edge.to) && (from.kind === 'space' || from.kind === 'query')) visible.add(edge.from);
  });

  return visible;
};

export const getTimelineSteps = (graph: HPGGraph): TimelineStep[] =>
  graph.nodes
    .map((node) => {
      const match = PROOF_STEP_ID.exec(node.id);
      if (!match || node.kind !== 'projection') return null;
      return {
        step: Number(match[1]),
        nodeId: node.id,
        label: node.label?.trim() || node.id,
      } as TimelineStep;
    })
    .filter((step): step is TimelineStep => Boolean(step))
    .sort((a, b) => a.step - b.step);

export const filterGraphByStep = (graph: HPGGraph, step: number | null, showFullGraph: boolean): StepFilterResult => {
  if (showFullGraph || step === null) {
    return { graph, newNodeIds: new Set<string>(), newEdgeIds: new Set<string>() };
  }

  const visibleNow = getVisibleNodeIdsUpToStep(graph, step);
  const visiblePrev = step > 0 ? getVisibleNodeIdsUpToStep(graph, step - 1) : new Set<string>();

  const nodes = graph.nodes.filter((node) => visibleNow.has(node.id));
  const edges = graph.edges.filter((edge) => visibleNow.has(edge.from) && visibleNow.has(edge.to));

  const newNodeIds = new Set([...visibleNow].filter((id) => !visiblePrev.has(id)));
  const prevEdgeKeys = new Set(
    graph.edges
      .filter((edge) => visiblePrev.has(edge.from) && visiblePrev.has(edge.to))
      .map((edge) => getEdgeKey(edge)),
  );
  const newEdgeIds = new Set(edges.map((edge) => getEdgeKey(edge)).filter((key) => !prevEdgeKeys.has(key)));

  return { graph: { nodes, edges }, newNodeIds, newEdgeIds };
};

export const getGoalHighlightSet = (graph: HPGGraph): Set<string> => {
  const queryIds = new Set(graph.nodes.filter((n) => n.kind === 'query').map((n) => n.id));
  const highlighted = new Set<string>(queryIds);

  graph.edges.forEach((edge) => {
    if (edge.type === 'supports_goal' && queryIds.has(edge.to)) {
      highlighted.add(edge.from);
      highlighted.add(edge.to);
    }
  });

  return highlighted;
};

export const filterGraph = (
  graph: HPGGraph,
  kindVisibility: KindVisibility,
  edgeVisibility: EdgeVisibility,
  search: string,
): HPGGraph => {
  const needle = search.trim().toLowerCase();

  const nodes = graph.nodes.filter((node) => {
    const kindEnabled = kindVisibility[node.kind] ?? true;
    if (!kindEnabled) return false;
    if (!needle) return true;
    return node.id.toLowerCase().includes(needle) || node.label.toLowerCase().includes(needle);
  });

  const allowed = new Set(nodes.map((node) => node.id));
  const edges = graph.edges.filter((edge) => {
    const typeEnabled = edgeVisibility[edge.type] ?? true;
    return typeEnabled && allowed.has(edge.from) && allowed.has(edge.to);
  });

  return { nodes, edges };
};

export const toFlowElements = (
  graph: HPGGraph,
  highlightGoalPath: boolean,
  emphasis?: { newNodeIds?: Set<string>; newEdgeIds?: Set<string> },
) => {
  const highlighted = highlightGoalPath ? getGoalHighlightSet(graph) : new Set<string>();
  const newNodeIds = emphasis?.newNodeIds ?? new Set<string>();
  const newEdgeIds = emphasis?.newEdgeIds ?? new Set<string>();
  const nodes = graph.nodes.map((node) => {
    const flowNode = nodeToFlowNode(node, highlighted.has(node.id));
    if (!newNodeIds.has(node.id)) return flowNode;
    return {
      ...flowNode,
      style: {
        ...flowNode.style,
        borderWidth: 3,
        boxShadow: '0 0 0 4px rgba(14,165,233,0.28)',
      },
    };
  });
  const edges = graph.edges.map((edge) => {
    const flowEdge = edgeToFlowEdge(
      edge,
      highlighted.has(edge.from) && highlighted.has(edge.to) && edge.type === 'supports_goal',
    );
    if (!newEdgeIds.has(getEdgeKey(edge))) return flowEdge;
    return {
      ...flowEdge,
      style: {
        ...(flowEdge.style ?? {}),
        strokeWidth: 3.6,
      },
    };
  });

  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'LR', ranksep: 90, nodesep: 40 });

  nodes.forEach((node) => dagreGraph.setNode(node.id, { width: 180, height: 56 }));
  edges.forEach((edge) => dagreGraph.setEdge(edge.source, edge.target));
  dagre.layout(dagreGraph);

  const layoutNodes = nodes.map((node) => {
    const position = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: position.x - 90, y: position.y - 28 },
    };
  });

  return { nodes: layoutNodes, edges };
};

export const downloadFilteredGraph = (graph: HPGGraph) => {
  const blob = new Blob([JSON.stringify(graph, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'hpg_filtered.json';
  anchor.click();
  URL.revokeObjectURL(url);
};
