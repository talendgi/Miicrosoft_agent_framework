import { useState, useEffect } from "react";
import { Trash2, X, AlertCircle, Activity, CheckCircle, XCircle, Clock } from "lucide-react";
import type { ExecutionRecord, Pipeline } from "../../types";

type Props = {
  executions: ExecutionRecord[];
  pipelines: Pipeline[];
  onDeleteExecution: (id: string) => void;
  onClearAll: () => void;
};

export function MonitoringPanel({ executions, onDeleteExecution, onClearAll }: Props) {
  const [selectedExecution, setSelectedExecution] = useState<ExecutionRecord | null>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle size={16} className="text-green-500" />;
      case "failed":
        return <XCircle size={16} className="text-red-500" />;
      case "running":
        return <Clock size={16} className="text-blue-500 animate-spin" />;
      default:
        return <Activity size={16} className="text-gray-500" />;
    }
  };

  const formatAuditLog = (log: string) => {
    // Extract key information without showing full data
    if (log.includes("Extracted")) {
      const match = log.match(/Extracted (\d+) records/);
      return match ? `📊 Extracted ${match[1]} records` : log;
    }
    if (log.includes("Loaded")) {
      const match = log.match(/Loaded (\d+) rows/);
      return match ? `✅ Loaded ${match[1]} rows` : log;
    }
    if (log.includes("FilterTransform")) {
      const match = log.match(/(\d+) -> (\d+) records/);
      return match ? `🔀 Filtered: ${match[1]} → ${match[2]} records` : log;
    }
    if (log.includes("Table") && log.includes("created")) {
      return `📋 Table created successfully`;
    }
    if (log.includes("Routing to")) {
      return `🔀 Routing decision made`;
    }
    return log;
  };

  const getAuditLogs = (execution: ExecutionRecord) => {
    if (!execution.logs) return [];
    return execution.logs.filter(log => 
      log.includes("Extracted") || 
      log.includes("Loaded") || 
      log.includes("FilterTransform") ||
      log.includes("created") ||
      log.includes("Routing") ||
      log.includes("Pipeline") ||
      log.includes("status=")
    );
  };

  return (
    <div className="monitoring-container">
      <div className="monitoring-header">
        <h2>Execution Monitoring</h2>
        <button className="btn-danger" onClick={() => setShowClearConfirm(true)}>
          <Trash2 size={16} /> Clear All
        </button>
      </div>

      {showClearConfirm && (
        <div className="modal-overlay" onClick={() => setShowClearConfirm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Clear All Execution Logs?</h3>
            <div className="modal-actions">
              <button onClick={() => setShowClearConfirm(false)}>Cancel</button>
              <button className="btn-danger" onClick={() => { onClearAll(); setShowClearConfirm(false); }}>
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="executions-timeline">
        {executions.map((execution) => (
          <div 
            key={execution.id} 
            className={`execution-card ${selectedExecution?.id === execution.id ? 'selected' : ''}`}
            onClick={() => setSelectedExecution(execution)}
          >
            <div className="execution-header">
              <div className="execution-title">
                {getStatusIcon(execution.status)}
                <h3>{execution.pipeline_name}</h3>
              </div>
              <div className="execution-meta">
                <span className={`status-badge ${execution.status}`}>{execution.status}</span>
                <span>{new Date(execution.started_at).toLocaleTimeString()}</span>
                {execution.finished_at && (
                  <span>
                    {Math.round((new Date(execution.finished_at).getTime() - new Date(execution.started_at).getTime()) / 1000)}s
                  </span>
                )}
              </div>
              <button 
                className="delete-execution"
                onClick={(e) => { e.stopPropagation(); onDeleteExecution(execution.id); }}
              >
                <X size={16} />
              </button>
            </div>

            {selectedExecution?.id === execution.id && (
              <div className="execution-details">
                <div className="audit-logs">
                  <h4>Execution Summary</h4>
                  <div className="log-list">
                    {getAuditLogs(execution).map((log: string, idx: number) => (
                      <div key={idx} className="log-item">
                        {formatAuditLog(log)}
                      </div>
                    ))}
                  </div>
                </div>

                {execution.node_results && (
                  <div className="node-timeline">
                    <h4>Node Execution Status</h4>
                    {execution.node_results.map((node: any) => (
                      <div key={node.node_id} className={`node-status-item ${node.status}`}>
                        <div className="node-info">
                          {getStatusIcon(node.status)}
                          <span className="node-name">{node.node_label}</span>
                        </div>
                        <div className="node-meta">
                          {node.output && (
                            <span className="node-output-summary">
                              {node.output.rows_loaded && `${node.output.rows_loaded} rows loaded`}
                              {node.output.filtered_count && `${node.output.filtered_count} records filtered`}
                              {node.output.record_count && `${node.output.record_count} records extracted`}
                            </span>
                          )}
                          <span>{new Date(node.started_at).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}