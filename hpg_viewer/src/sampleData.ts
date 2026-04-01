import { HPGGraph } from './types';

export const sampleData: HPGGraph = {
  nodes: [
    { id: 'space-euclid', label: 'Euclidean Space', kind: 'space' },
    { id: 'obj-triangle-abc', label: 'Triangle ABC', kind: 'object', object_type: 'triangle', space_id: 'space-euclid' },
    { id: 'view-angle', label: 'Angle View', kind: 'view', role: 'analysis', object_id: 'obj-triangle-abc' },
    {
      id: 'proj-bisector',
      label: 'Bisector Projection',
      kind: 'projection',
      projection_type: 'angle_bisector',
      object_id: 'obj-triangle-abc',
      space_id: 'space-euclid',
    },
    { id: 'fact-equal-angles', label: '∠ABD = ∠DBC', kind: 'fact', fact_type: 'equality', meta: { confidence: 0.92 } },
    { id: 'fact-support', label: 'D lies on BC', kind: 'fact', fact_type: 'incidence' },
    { id: 'query-goal', label: 'Prove AB = AC', kind: 'query' },
  ],
  edges: [
    { from: 'obj-triangle-abc', to: 'space-euclid', type: 'in_space' },
    { from: 'view-angle', to: 'obj-triangle-abc', type: 'interprets' },
    { from: 'proj-bisector', to: 'view-angle', type: 'uses' },
    { from: 'proj-bisector', to: 'fact-equal-angles', type: 'creates' },
    { from: 'obj-triangle-abc', to: 'fact-support', type: 'asserts' },
    { from: 'fact-support', to: 'fact-equal-angles', type: 'rewrites' },
    { from: 'fact-equal-angles', to: 'query-goal', type: 'supports_goal' },
    { from: 'fact-support', to: 'query-goal', type: 'supports_goal' },
    { from: 'fact-equal-angles', to: 'fact-support', type: 'derives' },
    { from: 'view-angle', to: 'proj-bisector', type: 'reinterprets' },
    { from: 'query-goal', to: 'view-angle', type: 'explores' },
  ],
};
