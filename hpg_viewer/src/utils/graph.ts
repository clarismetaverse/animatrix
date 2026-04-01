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

export const toFlowElements = (graph: HPGGraph, highlightGoalPath: boolean) => {
  const highlighted = highlightGoalPath ? getGoalHighlightSet(graph) : new Set<string>();
  const nodes = graph.nodes.map((node) => nodeToFlowNode(node, highlighted.has(node.id)));
  const edges = graph.edges.map((edge) =>
    edgeToFlowEdge(edge, highlighted.has(edge.from) && highlighted.has(edge.to) && edge.type === 'supports_goal'),
  );

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
