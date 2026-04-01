import { EdgeVisibility, KindVisibility } from '../types';

interface ControlsPanelProps {
  kindVisibility: KindVisibility;
  edgeVisibility: EdgeVisibility;
  search: string;
  highlightGoalPath: boolean;
  onToggleKind: (kind: string) => void;
  onToggleEdgeType: (type: string) => void;
  onSearchChange: (value: string) => void;
  onHighlightToggle: () => void;
  onResetFilters: () => void;
  onFitView: () => void;
  onExport: () => void;
}

export function ControlsPanel(props: ControlsPanelProps) {
  const {
    kindVisibility,
    edgeVisibility,
    search,
    highlightGoalPath,
    onToggleKind,
    onToggleEdgeType,
    onSearchChange,
    onHighlightToggle,
    onResetFilters,
    onFitView,
    onExport,
  } = props;

  return (
    <section className="panel">
      <h4>Controls</h4>
      <input
        className="search-input"
        placeholder="Search by id or label"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
      />

      <details open>
        <summary>Node kinds</summary>
        {Object.keys(kindVisibility).map((kind) => (
          <label key={kind} className="checkbox-row">
            <input type="checkbox" checked={kindVisibility[kind]} onChange={() => onToggleKind(kind)} /> {kind}
          </label>
        ))}
      </details>

      <details>
        <summary>Edge types</summary>
        {Object.keys(edgeVisibility).map((type) => (
          <label key={type} className="checkbox-row">
            <input type="checkbox" checked={edgeVisibility[type]} onChange={() => onToggleEdgeType(type)} /> {type}
          </label>
        ))}
      </details>

      <label className="checkbox-row">
        <input type="checkbox" checked={highlightGoalPath} onChange={onHighlightToggle} /> highlight goal path
      </label>

      <div className="button-row">
        <button onClick={onFitView}>Fit view</button>
        <button onClick={onResetFilters}>Reset filters</button>
        <button onClick={onExport}>Export filtered JSON</button>
      </div>
    </section>
  );
}
