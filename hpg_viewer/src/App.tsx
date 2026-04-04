import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  filterGraphByStep,
  getDefaultEdgeVisibility,
  getDefaultKindVisibility,
  getTimelineSteps,
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
  const [currentStep, setCurrentStep] = useState<number | null>(null);
  const [showFullGraph, setShowFullGraph] = useState(true);

  const [kindVisibility, setKindVisibility] = useState<KindVisibility>(() => getDefaultKindVisibility(sampleData.nodes));
  const [edgeVisibility, setEdgeVisibility] = useState<EdgeVisibility>(() => getDefaultEdgeVisibility(sampleData.edges));

  const flowRef = useRef<ReactFlowInstance | null>(null);
  const timelineSteps = useMemo(() => getTimelineSteps(graph), [graph]);

  useEffect(() => {
    if (!timelineSteps.length) {
      setCurrentStep(null);
      setShowFullGraph(true);
      return;
    }
    const maxStep = timelineSteps[timelineSteps.length - 1].step;
    setCurrentStep(maxStep);
    setShowFullGraph(false);
  }, [timelineSteps]);

  const timelineFiltered = useMemo(
    () => filterGraphByStep(graph, currentStep, showFullGraph || !timelineSteps.length),
    [graph, currentStep, showFullGraph, timelineSteps.length],
  );

  const filteredGraph = useMemo(
    () => filterGraph(timelineFiltered.graph, kindVisibility, edgeVisibility, search),
    [timelineFiltered.graph, kindVisibility, edgeVisibility, search],
  );
  const visibleNodeIds = useMemo(() => new Set(filteredGraph.nodes.map((node) => node.id)), [filteredGraph.nodes]);
  const visibleEdgeIds = useMemo(
    () =>
      new Set(
        filteredGraph.edges.map((edge) => `${edge.from}-${edge.to}-${edge.type}`),
      ),
    [filteredGraph.edges],
  );
  const flowData = useMemo(
    () =>
      toFlowElements(filteredGraph, highlightGoalPath, {
        newNodeIds: new Set([...timelineFiltered.newNodeIds].filter((id) => visibleNodeIds.has(id))),
        newEdgeIds: new Set([...timelineFiltered.newEdgeIds].filter((id) => visibleEdgeIds.has(id))),
      }),
    [filteredGraph, highlightGoalPath, timelineFiltered.newNodeIds, timelineFiltered.newEdgeIds, visibleEdgeIds, visibleNodeIds],
  );
  const currentStepMeta = useMemo(
    () => timelineSteps.find((step) => step.step === currentStep) ?? null,
    [timelineSteps, currentStep],
  );

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
          {timelineSteps.length > 0 && (
            <section className="panel">
              <h4>Proof timeline</h4>
              <div className="button-row">
                <button
                  onClick={() => setCurrentStep((prev) => (prev === null ? 0 : Math.max(0, prev - 1)))}
                  disabled={showFullGraph || currentStep === null || currentStep <= timelineSteps[0].step}
                >
                  Previous
                </button>
                <button
                  onClick={() =>
                    setCurrentStep((prev) =>
                      prev === null ? timelineSteps[0].step : Math.min(timelineSteps[timelineSteps.length - 1].step, prev + 1),
                    )
                  }
                  disabled={
                    showFullGraph ||
                    currentStep === null ||
                    currentStep >= timelineSteps[timelineSteps.length - 1].step
                  }
                >
                  Next
                </button>
              </div>
              <label className="step-picker-label" htmlFor="step-picker">
                Step
              </label>
              <select
                id="step-picker"
                className="step-picker"
                value={currentStep ?? timelineSteps[timelineSteps.length - 1].step}
                onChange={(event) => setCurrentStep(Number(event.target.value))}
                disabled={showFullGraph}
              >
                {timelineSteps.map((step) => (
                  <option key={step.nodeId} value={step.step}>
                    {step.step}: {step.label}
                  </option>
                ))}
              </select>
              <label className="checkbox-row">
                <input type="checkbox" checked={showFullGraph} onChange={() => setShowFullGraph((prev) => !prev)} /> show
                full graph
              </label>
              <p className="muted">
                {currentStepMeta ? `Step ${currentStepMeta.step}: ${currentStepMeta.label}` : 'Select a step to inspect proof growth.'}
              </p>
            </section>
          )}

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

        <Sidebar node={selectedNode} step={currentStepMeta} />
      </div>
    </div>
  );
}

export default App;
