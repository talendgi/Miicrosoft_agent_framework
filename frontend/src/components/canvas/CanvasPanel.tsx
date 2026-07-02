import { useEffect, useMemo, useState, useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
} from "reactflow";
import "reactflow/dist/style.css";
// or
// import "reactflow/dist/base.css";
// Or 
// import "./styles/reactflow.css";
import type { Connection as StudioConnection, Pipeline } from "../../types";
import { WorkflowNode } from "./WorkflowNode";

type Props = {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  onChange: (value: { nodes: Node[]; edges: Edge[] }) => void;
  onLoadPipeline: (pipeline: Pipeline) => void;
  pipelines: Pipeline[];
  connections: StudioConnection[];
  onAddExecutor: (type: string) => void;
  pipelineName: string;
  onRenamePipeline: (name: string) => void;
};

export function CanvasPanel({
  nodes,
  edges,
  selectedNodeId,
  setSelectedNodeId,
  onChange,
  onLoadPipeline,
  pipelines,
  onAddExecutor,
  pipelineName,
  onRenamePipeline,
}: Props) {
  const nodeTypes = useMemo(() => ({ workflowNode: WorkflowNode }), []);
  const [flowNodes, setFlowNodes] = useState<Node[]>(nodes);
  const [flowEdges, setFlowEdges] = useState<Edge[]>(edges);

  useEffect(() => {
    setFlowNodes(nodes);
    setFlowEdges(edges);
  }, [edges, nodes]);

  const syncNodes = (nextNodes: Node[], nextEdges: Edge[]) => {
    setFlowNodes(nextNodes);
    setFlowEdges(nextEdges);
    onChange({ nodes: nextNodes, edges: nextEdges });
  };

  // Handle deleting a node and its connected edges
  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      const newNodes = flowNodes.filter((node) => node.id !== nodeId);
      const newEdges = flowEdges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      );

      syncNodes(newNodes, newEdges);

      if (selectedNodeId === nodeId) {
        setSelectedNodeId(null);
      }
    },
    [flowNodes, flowEdges, selectedNodeId, setSelectedNodeId]
  );

  return (
    <div className="canvas-shell">
      <div className="canvas-topbar">
        <div className="canvas-title-block">
          <h2>Workflow Designer</h2>
          <p>Drag executors into the canvas, connect them, and run ETL pipelines.</p>
          <label className="pipeline-name-field">
            <span>Pipeline Name</span>
            <input
              value={pipelineName}
              onChange={(event) => onRenamePipeline(event.target.value)}
              placeholder="Untitled Pipeline"
            />
          </label>
        </div>
        <select
          className="select-control"
          defaultValue=""
          onChange={(event) => {
            const pipeline = pipelines.find((item) => item.id === event.target.value);
            if (pipeline) {
              onLoadPipeline(pipeline);
              // Note: pipeline.nodes/edges might need mapping if they are backend format
              // Assuming they are already canvas format for this example
              syncNodes(pipeline.nodes as any, pipeline.edges as any);
            }
          }}
        >
          <option value="" disabled>
            Load saved pipeline
          </option>
          {pipelines.map((pipeline) => (
            <option key={pipeline.id} value={pipeline.id}>
              {pipeline.name}
            </option>
          ))}
        </select>
      </div>
      <div className="reactflow-wrapper">
        <ReactFlow
          // Inject the onDelete handler into every node's data
          nodes={flowNodes.map((node) => ({
            ...node,
            data: {
              ...node.data,
              onDelete: handleDeleteNode,
            },
          }))}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          onDragOver={(event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = "copy";
          }}
          onDrop={(event) => {
            event.preventDefault();
            const executorType = event.dataTransfer.getData("application/workflow-executor");
            if (!executorType) {
              return;
            }
            onAddExecutor(executorType);
          }}
          onNodesChange={(changes: NodeChange[]) => {
            setFlowNodes((currentNodes) => {
              const nextNodes = applyNodeChanges(changes, currentNodes);
              onChange({ nodes: nextNodes, edges: flowEdges });
              return nextNodes;
            });
          }}
          onEdgesChange={(changes: EdgeChange[]) => {
            setFlowEdges((currentEdges) => {
              const nextEdges = applyEdgeChanges(changes, currentEdges);
              onChange({ nodes: flowNodes, edges: nextEdges });
              return nextEdges;
            });
          }}
          onConnect={(connection: Connection) => {
            const nextEdges = addEdge(connection, flowEdges);
            syncNodes(flowNodes, nextEdges);
          }}
          onNodeClick={(_, node) => setSelectedNodeId(node.id)}
          onPaneClick={() => setSelectedNodeId(null)}
          fitView
        >
          <Background gap={18} size={1} color="#2d364a" />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}