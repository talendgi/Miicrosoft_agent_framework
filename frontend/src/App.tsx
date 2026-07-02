import { useEffect, useMemo, useState } from "react";
import { Workflow, Database, GitBranch, Activity, Save, Play, Plus, Search, PanelLeftClose, PanelRightClose } from "lucide-react";
import type { Connection, ExecutionRecord, Pipeline } from "./types";
import { api } from "./api";
import { executorCatalog, buildNodeData } from "./data/executors";
import { CanvasPanel } from "./components/canvas/CanvasPanel";
import { Header } from "./components/Header";
import { ConnectionsPanel } from "./components/connections/ConnectionsPanel";
import { PipelineLibraryPanel } from "./components/library/PipelineLibraryPanel";
import { MonitoringPanel } from "./components/monitoring/MonitoringPanel";
import { PropertiesPanel } from "./components/panels/PropertiesPanel";
import { NodePalette } from "./components/panels/NodePalette";
import { Modal } from "./components/Modal";
import { v4 as uuidv4 } from "./utils/uuid";
import { toBackendEdge, toBackendNode, toCanvasEdge, toCanvasNode } from "./utils/pipelineMapping";

type TabKey = "canvas" | "connections" | "pipelines" | "monitoring";

export default function App() {
  const [tab, setTab] = useState<TabKey>("canvas");
  const [connections, setConnections] = useState<Connection[]>([]);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [search, setSearch] = useState("");
  const [isConnectionModalOpen, setConnectionModalOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState<Connection | null>(null);
  const [canvasSnapshot, setCanvasSnapshot] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [activePipeline, setActivePipeline] = useState<Pipeline | null>(null);
  const [pipelineName, setPipelineName] = useState("Untitled Pipeline");
  const [loading, setLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState("Ready for ETL composition");
  const [isDirty, setIsDirty] = useState(false);

  const filteredExecutors = useMemo(
    () =>
      executorCatalog.filter((item) =>
        [item.label, item.category, item.description].some((value) => value.toLowerCase().includes(search.toLowerCase())),
      ),
    [search],
  );

  useEffect(() => {
    Promise.all([api.connections.list(), api.pipelines.list(), api.executions.list()])
      .then(([connectionList, pipelineList, executionList]) => {
        setConnections(connectionList);
        setPipelines(pipelineList);
        setExecutions(executionList);
      })
      .finally(() => setLoading(false));
  }, []);

  const refreshLibrary = async () => {
    const [connectionList, pipelineList, executionList] = await Promise.all([
      api.connections.list(), 
      api.pipelines.list(), 
      api.executions.list()
    ]);
    setConnections(connectionList);
    setPipelines(pipelineList);
    setExecutions(executionList);
  };

  const onSavePipeline = async (): Promise<Pipeline> => {
    try {
      setStatusMessage("Saving pipeline...");
      const payload = {
        name: pipelineName.trim() || "Untitled Pipeline",
        description: activePipeline?.description ?? "Compose ETL workflow with reusable executors.",
        connection_id: activePipeline?.connection_id ?? connections[0]?.id ?? null,
        nodes: canvasSnapshot.nodes.map(toBackendNode),
        edges: canvasSnapshot.edges.map(toBackendEdge),
      };

      if (activePipeline?.id) {
        const saved = await api.pipelines.update(activePipeline.id, payload);
        setActivePipeline(saved);
        setPipelineName(saved.name);
        setIsDirty(false);
        await refreshLibrary();
        setStatusMessage(`Pipeline saved: ${saved.name}`);
        return saved;
      }

      const saved = await api.pipelines.create(payload);
      setActivePipeline(saved);
      setPipelineName(saved.name);
      setIsDirty(false);
      await refreshLibrary();
      setStatusMessage(`Pipeline created: ${saved.name}`);
      return saved;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to save pipeline.";
      setStatusMessage(message);
      throw error;
    }
  };

  const onRunPipeline = async () => {
    try {
      setStatusMessage("Running pipeline...");
      if (!activePipeline?.id) {
        const saved = await onSavePipeline();
        const result = await api.pipelines.run(saved.id);
        setExecutions((current) => [result.execution, ...current]);
        await refreshLibrary();
        setTab("monitoring");
        setStatusMessage(`Pipeline run completed: ${saved.name}`);
        return;
      }
      const result = await api.pipelines.run(activePipeline.id);
      setExecutions((current) => [result.execution, ...current]);
      await refreshLibrary();
      setTab("monitoring");
      setStatusMessage(`Pipeline run completed: ${activePipeline.name}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to run pipeline.";
      setStatusMessage(message);
    }
  };

  const onDeleteExecution = async (executionId: string) => {
    try {
      await api.executions.delete(executionId);
      setExecutions((current) => current.filter((e) => e.id !== executionId));
      setStatusMessage("Execution log deleted");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to delete execution.";
      setStatusMessage(message);
    }
  };

  const onClearAllExecutions = async () => {
    try {
      await api.executions.clearAll();
      setExecutions([]);
      setStatusMessage("All execution logs cleared");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to clear executions.";
      setStatusMessage(message);
    }
  };

  const openConnectionEditor = (connection?: Connection) => {
    setEditingConnection(connection ?? null);
    setConnectionModalOpen(true);
  };

  const addExecutorNode = (type: string) => {
    const executor = executorCatalog.find((item) => item.type === type);
    if (!executor) {
      return;
    }

    setTab("canvas");
    setCanvasSnapshot((current) => ({
      ...current,
      nodes: [
        ...current.nodes,
        {
          id: uuidv4(),
          type: "workflowNode",
          position: { x: 240, y: 120 + current.nodes.length * 120 },
          data: buildNodeData(executor.type, executor.label),
        },
      ],
    }));
    setIsDirty(true);
  };

  const loadPipelineIntoCanvas = (pipeline: Pipeline) => {
    setActivePipeline(pipeline);
    setPipelineName(pipeline.name);
    setCanvasSnapshot({
      nodes: (pipeline.nodes ?? []).map(toCanvasNode),
      edges: (pipeline.edges ?? []).map(toCanvasEdge),
    });
    setSelectedNodeId(null);
    setTab("canvas");
    setStatusMessage(`Loaded pipeline: ${pipeline.name}`);
    setIsDirty(false);
  };

  const renamePipeline = (name: string) => {
    setPipelineName(name);
    setActivePipeline((current) => (current ? { ...current, name } : current));
    setIsDirty(true);
  };

  const handleCanvasChange = (nextValue: { nodes: any[]; edges: any[] }) => {
    setCanvasSnapshot(nextValue);
    setIsDirty(true);
  };

  return (
    <div className="studio-shell">
      <Header
        activeTab={tab}
        onTabChange={setTab}
        onSave={() => {
          void onSavePipeline();
        }}
        onRun={() => {
          void onRunPipeline();
        }}
        onNewWorkflow={() => {
          setActivePipeline(null);
          setPipelineName("Untitled Pipeline");
          setCanvasSnapshot({ nodes: [], edges: [] });
          setSelectedNodeId(null);
          setTab("canvas");
          setStatusMessage("Started a new workflow");
          setIsDirty(false);
        }}
      />

      <div
        className="workspace"
        style={{
          gridTemplateColumns: `${leftCollapsed ? "56px" : "clamp(260px, 23vw, 320px)"} minmax(0, 1fr) ${rightCollapsed ? "56px" : "clamp(300px, 24vw, 360px)"}`,
        }}
      >
        <aside className={`sidebar left ${leftCollapsed ? "collapsed" : ""}`}>
          <div className="sidebar-toolbar">
            <button className="icon-button" onClick={() => setLeftCollapsed((value) => !value)}>
              {leftCollapsed ? <PanelRightClose size={18} /> : <PanelLeftClose size={18} />}
            </button>
            {!leftCollapsed && (
              <div className="sidebar-header-copy">
                <div>
                  <div className="sidebar-title">Executors</div>
                  <div className="sidebar-subtitle">Drag components into the canvas</div>
                </div>
              </div>
            )}
          </div>
          {!leftCollapsed && (
            <>
              <div className="sidebar-search">
                <label className="search-box">
                  <Search size={14} />
                  <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search executors" />
                </label>
              </div>
              <NodePalette items={filteredExecutors} onCreateNode={addExecutorNode} />
            </>
          )}
        </aside>

        <main className="canvas-stage">
          {tab === "canvas" && (
            <CanvasPanel
              nodes={canvasSnapshot.nodes}
              edges={canvasSnapshot.edges}
              selectedNodeId={selectedNodeId}
              setSelectedNodeId={setSelectedNodeId}
              onChange={handleCanvasChange}
              onAddExecutor={addExecutorNode}
              onLoadPipeline={loadPipelineIntoCanvas}
              pipelines={pipelines}
              connections={connections}
              pipelineName={pipelineName}
              onRenamePipeline={renamePipeline}
            />
          )}
          {tab === "connections" && <ConnectionsPanel connections={connections} onEdit={openConnectionEditor} onCreate={() => openConnectionEditor()} onRefresh={refreshLibrary} />}
          {tab === "pipelines" && (
            <PipelineLibraryPanel
              pipelines={pipelines}
              onRun={async (pipeline) => {
                await api.pipelines.run(pipeline.id);
                await refreshLibrary();
                setTab("monitoring");
                setStatusMessage(`Pipeline run completed: ${pipeline.name}`);
              }}
              onLoad={loadPipelineIntoCanvas}
              onDelete={async (id) => {
                await api.pipelines.remove(id);
                await refreshLibrary();
                setStatusMessage("Pipeline deleted");
              }}
            />
          )}
          {tab === "monitoring" && (
            <MonitoringPanel 
              executions={executions} 
              pipelines={pipelines}
              onDeleteExecution={onDeleteExecution}
              onClearAll={onClearAllExecutions}
            />
          )}
        </main>

        <aside className={`sidebar right ${rightCollapsed ? "collapsed" : ""}`}>
          <div className="sidebar-toolbar">
            <button className="icon-button" onClick={() => setRightCollapsed((value) => !value)}>
              {rightCollapsed ? <PanelLeftClose size={18} /> : <PanelRightClose size={18} />}
            </button>
            {!rightCollapsed && (
              <div>
                <div className="sidebar-title">Node Properties</div>
                <div className="sidebar-subtitle">Configure the selected executor</div>
              </div>
            )}
          </div>
          {!rightCollapsed && (
            <div className="sidebar-content">
              <PropertiesPanel
                selectedNodeId={selectedNodeId}
                nodes={canvasSnapshot.nodes}
                connections={connections}
                onUpdateNode={(nodeId, nextData) =>
                  setCanvasSnapshot((current) => {
                    const nextState = {
                      ...current,
                      nodes: current.nodes.map((node) => {
                        if (node.id !== nodeId) {
                          return node;
                        }

                        return {
                          ...node,
                          data: {
                            ...node.data,
                            ...nextData,
                            config: nextData.config ? { ...node.data.config, ...nextData.config } : node.data.config,
                          },
                        };
                      }),
                    };
                    setIsDirty(true);
                    return nextState;
                  })
                }
                onApplyConfiguration={(nodeId) => {
                  const node = canvasSnapshot.nodes.find((item) => item.id === nodeId);
                  setStatusMessage(node ? `Applied configuration for ${node.data.label ?? "node"}` : "Applied configuration");
                  setIsDirty(true);
                }}
              />
            </div>
          )}
        </aside>
      </div>

      <div className="status-bar">
        <div className="status-item">
          <Workflow size={15} />
          <span>{pipelines.length} saved pipelines</span>
        </div>
        <div className="status-item">
          <Database size={15} />
          <span>{connections.length} connections</span>
        </div>
        <div className="status-item">
          <Activity size={15} />
          <span>{executions.length} executions</span>
        </div>
        {loading ? (
          <span className="status-muted">Loading studio state...</span>
        ) : (
          <span className="status-muted">{isDirty ? `Unsaved changes · ${statusMessage}` : statusMessage}</span>
        )}
      </div>

      {isConnectionModalOpen && (
        <Modal
          title={editingConnection ? "Edit Connection" : "Add Connection"}
          onClose={() => {
            setConnectionModalOpen(false);
            setEditingConnection(null);
          }}
        >
          <ConnectionsPanel
            connections={connections}
            onEdit={openConnectionEditor}
            onCreate={() => openConnectionEditor()}
            onRefresh={refreshLibrary}
            modalConnection={editingConnection}
            onModalClose={() => {
              setConnectionModalOpen(false);
              setEditingConnection(null);
            }}
          />
        </Modal>
      )}
    </div>
  );
}