import { HPGNode } from '../types';
import { TimelineStep } from '../utils/graph';

interface SidebarProps {
  node: HPGNode | null;
  step: TimelineStep | null;
}

const ignored = new Set(['id', 'label', 'kind']);

export function Sidebar({ node, step }: SidebarProps) {
  if (!node) {
    return (
      <aside className="sidebar">
        <h3>Inspector</h3>
        {step && (
          <div className="panel compact-panel">
            <h4>Current step</h4>
            <div className="kv"><strong>step</strong><span>{step.step}</span></div>
            <div className="kv"><strong>label</strong><span>{step.label}</span></div>
            <div className="kv"><strong>id</strong><span>{step.nodeId}</span></div>
          </div>
        )}
        <p>Select a node to inspect fields.</p>
      </aside>
    );
  }

  const extras = Object.entries(node).filter(([k]) => !ignored.has(k));

  return (
    <aside className="sidebar">
      <h3>Inspector</h3>
      {step && (
        <div className="panel compact-panel">
          <h4>Current step</h4>
          <div className="kv"><strong>step</strong><span>{step.step}</span></div>
          <div className="kv"><strong>label</strong><span>{step.label}</span></div>
          <div className="kv"><strong>id</strong><span>{step.nodeId}</span></div>
        </div>
      )}
      <div className="kv"><strong>id</strong><span>{node.id}</span></div>
      <div className="kv"><strong>label</strong><span>{node.label}</span></div>
      <div className="kv"><strong>kind</strong><span>{node.kind}</span></div>
      {node.kind === 'projection' && (
        <>
          <div className="kv"><strong>space_id</strong><span>{String(node.space_id ?? '—')}</span></div>
          <div className="kv"><strong>projection_type</strong><span>{String(node.projection_type ?? '—')}</span></div>
        </>
      )}
      {extras.map(([key, value]) => (
        <div className="kv" key={key}>
          <strong>{key}</strong>
          <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
        </div>
      ))}
    </aside>
  );
}
