import { HPGNode } from '../types';

interface SidebarProps {
  node: HPGNode | null;
}

const ignored = new Set(['id', 'label', 'kind']);

export function Sidebar({ node }: SidebarProps) {
  if (!node) {
    return (
      <aside className="sidebar">
        <h3>Inspector</h3>
        <p>Select a node to inspect fields.</p>
      </aside>
    );
  }

  const extras = Object.entries(node).filter(([k]) => !ignored.has(k));

  return (
    <aside className="sidebar">
      <h3>Inspector</h3>
      <div className="kv"><strong>id</strong><span>{node.id}</span></div>
      <div className="kv"><strong>label</strong><span>{node.label}</span></div>
      <div className="kv"><strong>kind</strong><span>{node.kind}</span></div>
      {extras.map(([key, value]) => (
        <div className="kv" key={key}>
          <strong>{key}</strong>
          <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
        </div>
      ))}
    </aside>
  );
}
