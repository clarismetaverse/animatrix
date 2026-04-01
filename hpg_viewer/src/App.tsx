import { useCallback, useMemo, useRef, useState } from 'react';
import ReactFlow, { Background, Controls, MiniMap, ReactFlowInstance } from 'reactflow';
import 'reactflow/dist/style.css';
import { ControlsPanel } from './components/ControlsPanel';
import { Legend } from './components/Legend';
import { Sidebar } from './components/Sidebar';
import { sampleData } from './sampleData';
import { EdgeVisibility, HPGGraph, HPGNode, KindVisibility } from './types';
import {
  downloadFilteredGraph,
  filterGraph,
  getDefaultEdgeVisibility,
  getDefaultKindVisibility,
  toFlowElements,
} from './utils/graph';

const parseJson = (text: string): HPGGraph | null => {
  try {
    const parsed = JSON.parse(text) as HPGGraph;
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) return null;
    return parsed;
  } catch {
    return null;
  }
};

function App() {
  const [graph, setGraph] = useState<HPGGraph>(sampleData);
  const [selectedNode, setSelectedNode] = useState<HPGNode | null>(null);
  const [search, setSearch] = useState('');
  const [highlightGoalPath, setHighlightGoalPath] = useState(true);
  const [jsonInput, setJsonInput] = useState('');

  const [kindVisibility, setKindVisibility] = useState<KindVisibility>(() => getDefaultKindVisibility(sampleData.nodes));
  const [edgeVisibility, setEdgeVisibility] = useState<EdgeVisibility>(() => getDefaultEdgeVisibility(sampleData.edges));

  const flowRef = useRef<ReactFlowInstance | null>(null);

  const filteredGraph = useMemo(
    () => filterGraph(graph, kindVisibility, edgeVisibility, search),
    [graph, kindVisibility, edgeVisibility, search],
  );
  const flowData = useMemo(() => toFlowElements(filteredGraph, highlightGoalPath), [filteredGraph, highlightGoalPath]);

  const resetFilters = useCallback(() => {
    setSearch('');
    setKindVisibility(getDefaultKindVisibility(graph.nodes));
    setEdgeVisibility(getDefaultEdgeVisibility(graph.edges));
    setHighlightGoalPath(true);
  }, [graph]);

  const loadGraph = useCallback((next: HPGGraph) => {
    setGraph(next);
    setSelectedNode(null);
    setKindVisibility(getDefaultKindVisibility(next.nodes));
    setEdgeVisibility(getDefaultEdgeVisibility(next.edges));
  }, []);

  const onPasteLoad = () => {
    const next = parseJson(jsonInput);
    if (!next) {
      window.alert('Invalid HPG JSON. Expected { nodes: [], edges: [] }.');
      return;
    }
    loadGraph(next);
  };

  const onFileLoad: React.ChangeEventHandler<HTMLInputElement> = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const next = parseJson(text);
    if (!next) {
      window.alert('File does not contain a valid HPG JSON.');
      return;
    }
    setJsonInput(text);
    loadGraph(next);
  };

  return (
    <div className="app-shell">
      <header>
        <h1>HPG Viewer</h1>
      </header>
      <div className="layout">
        <div className="left-panel">
          <ControlsPanel
            kindVisibility={kindVisibility}
            edgeVisibility={edgeVisibility}
            search={search}
            highlightGoalPath={highlightGoalPath}
            onToggleKind={(kind) => setKindVisibility((prev) => ({ ...prev, [kind]: !prev[kind] }))}
            onToggleEdgeType={(type) => setEdgeVisibility((prev) => ({ ...prev, [type]: !prev[type] }))}
            onSearchChange={setSearch}
            onHighlightToggle={() => setHighlightGoalPath((prev) => !prev)}
            onResetFilters={resetFilters}
            onFitView={() => flowRef.current?.fitView({ padding: 0.2, duration: 300 })}
            onExport={() => downloadFilteredGraph(filteredGraph)}
          />

          <Legend />

          <section className="panel">
            <h4>Load JSON</h4>
            <textarea
              rows={8}
              value={jsonInput}
              onChange={(event) => setJsonInput(event.target.value)}
              placeholder="Paste exported HPG JSON here"
            />
            <div className="button-row">
              <button onClick={onPasteLoad}>Load pasted JSON</button>
              <input type="file" accept="application/json,.json" onChange={onFileLoad} />
            </div>
          </section>
        </div>

        <main className="graph-panel">
          <ReactFlow
            nodes={flowData.nodes}
            edges={flowData.edges}
            fitView
            onInit={(instance) => (flowRef.current = instance)}
            onNodeClick={(_, node) => {
              const match = graph.nodes.find((entry) => entry.id === node.id) ?? null;
              setSelectedNode(match);
            }}
          >
            <Background />
            <MiniMap pannable zoomable />
            <Controls />
          </ReactFlow>
        </main>

        <Sidebar node={selectedNode} />
      </div>
    </div>
  );
}

export default App;
