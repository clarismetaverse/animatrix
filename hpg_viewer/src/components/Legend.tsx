const nodeKinds = [
  ['space', '#7c3aed'],
  ['object', '#2563eb'],
  ['view', '#0891b2'],
  ['projection', '#ea580c'],
  ['fact', '#16a34a'],
  ['query', '#dc2626'],
] as const;

const edgeTypes = [
  'in_space',
  'interprets',
  'uses',
  'creates',
  'asserts',
  'rewrites',
  'derives',
  'supports_goal',
  'reinterprets',
  'explores',
];

export function Legend() {
  return (
    <section className="panel">
      <h4>Legend</h4>
      <div className="legend-grid">
        {nodeKinds.map(([kind, color]) => (
          <div key={kind} className="legend-item">
            <span className="dot" style={{ background: color }} /> {kind}
          </div>
        ))}
      </div>
      <p className="muted">Edges: {edgeTypes.join(', ')}</p>
    </section>
  );
}
