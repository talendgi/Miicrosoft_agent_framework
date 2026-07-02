import { Handle, Position, type NodeProps } from "reactflow";

// export function WorkflowNode({ data, selected }: NodeProps) {
//   return (
//     <div className={`workflow-node ${selected ? "selected" : ""}`}>
//       <Handle type="target" position={Position.Left} />
//       <div className="workflow-node-header">
//         <div className="workflow-node-label">{data.label}</div>
//         <div className="workflow-node-type">{data.executorType}</div>
//       </div>
//       <div className="workflow-node-description">{data.description}</div>
//       <div className="workflow-node-footer">Click to edit configuration</div>
//       <Handle type="source" position={Position.Right} />
//     </div>
//   );
// }

import { Trash2 } from "lucide-react";

export function WorkflowNode({ data, selected }: NodeProps) {
  // Cast data to include our custom onDelete function
  const { label, executorType, description, onDelete } = data as any;

  return (
    <div className={`workflow-node ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      
      <div className="node-header">
        <div className="node-title">
          <h3>{label}</h3>
          <span className="node-type">{executorType}</span>
        </div>
        {/* Delete Button */}
        <button
          className="node-delete-btn"
          onClick={(e) => {
            e.stopPropagation(); // Prevent node selection when clicking delete
            e.preventDefault();
            if (onDelete) onDelete(data.id); // Call the handler from CanvasPanel
          }}
          title="Delete node"
        >
          <Trash2 size={14} />
        </button>
      </div>
      
      <p className="node-description">{description}</p>
      
      <Handle type="source" position={Position.Right} />
    </div>
  );
}