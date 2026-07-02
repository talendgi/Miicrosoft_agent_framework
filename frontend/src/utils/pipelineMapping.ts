import type { Edge, Node } from "reactflow";

export const toBackendNode = (node: Node) => ({
  id: node.id,
  type: node.data.executor_type ?? node.data.executorType ?? node.type,
  label: node.data.label ?? node.data.executorType ?? node.type ?? "Node",
  position: node.position,
  data: {
    ...node.data,
    label: node.data.label ?? node.data.executorType ?? node.type ?? "Node",
    executor_type: node.data.executor_type ?? node.data.executorType ?? node.type,
  },
});

export const toBackendEdge = (edge: Edge) => ({
  id: edge.id,
  source: edge.source,
  target: edge.target,
  source_handle: edge.sourceHandle ?? null,
  target_handle: edge.targetHandle ?? null,
});

export const toCanvasNode = (node: any): Node => ({
  id: node.id,
  type: "workflowNode",
  position: node.position ?? { x: 0, y: 0 },
  data: {
    ...node.data,
    label: node.data?.label ?? node.label ?? node.type ?? "Node",
    executorType: node.data?.executor_type ?? node.data?.executorType ?? node.type,
    executor_type: node.data?.executor_type ?? node.data?.executorType ?? node.type,
  },
});

export const toCanvasEdge = (edge: any): Edge => ({
  id: edge.id,
  source: edge.source,
  target: edge.target,
  sourceHandle: edge.source_handle ?? edge.sourceHandle ?? null,
  targetHandle: edge.target_handle ?? edge.targetHandle ?? null,
});
