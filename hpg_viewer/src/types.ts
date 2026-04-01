export type HPGNodeKind = 'space' | 'object' | 'view' | 'projection' | 'fact' | 'query' | string;

export interface HPGNode {
  id: string;
  label: string;
  kind: HPGNodeKind;
  object_type?: string;
  role?: string;
  object_id?: string;
  space_id?: string;
  projection_type?: string;
  fact_type?: string;
  meta?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface HPGEdge {
  from: string;
  to: string;
  type: string;
  [key: string]: unknown;
}

export interface HPGGraph {
  nodes: HPGNode[];
  edges: HPGEdge[];
}

export type KindVisibility = Record<string, boolean>;
export type EdgeVisibility = Record<string, boolean>;
