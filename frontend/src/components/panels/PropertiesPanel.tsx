import { useEffect, useMemo, useState } from "react";
import type { Connection } from "../../types";

type Props = {
  selectedNodeId: string | null;
  nodes: any[];
  connections: Connection[];
  onUpdateNode: (nodeId: string, nextData: Record<string, unknown>) => void;
  onApplyConfiguration: (nodeId: string) => void;
};

type ConfigState = {
  connection: string;
  table: string;
  columns: string;
  destination_table: string;
  mode: string;
  limit: string;
  routes_true: string;
  routes_false: string;
};

const defaultConfigState: ConfigState = {
  connection: "",
  table: "",
  columns: "",
  destination_table: "",
  mode: "append",
  limit: "10",
  routes_true: "",
  routes_false: "",
};

export function PropertiesPanel({ selectedNodeId, nodes, connections, onUpdateNode, onApplyConfiguration }: Props) {
  const node = nodes.find((item) => item.id === selectedNodeId);
  const [configText, setConfigText] = useState("");
  const [configError, setConfigError] = useState("");
  const [formState, setFormState] = useState<ConfigState>(defaultConfigState);

  const executorType = node?.data?.executorType ?? "";

  const syncFormFromNode = useMemo(() => {
    if (!node) {
      return defaultConfigState;
    }

    const config = node.data.config ?? {};
    const routes = config.routes ?? {};
    
    return {
      connection: String(config.connection ?? ""),
      table: String(config.table ?? ""),
      columns: Array.isArray(config.columns) ? config.columns.join(", ") : String(config.columns ?? ""),
      destination_table: String(config.destination_table ?? ""),
      mode: String(config.mode ?? "append"),
      limit: String(config.limit ?? 10),
      routes_true: String(routes.true ?? ""),
      routes_false: String(routes.false ?? ""),
    };
  }, [node]);

  useEffect(() => {
    if (!node) {
      return;
    }

    setConfigText(JSON.stringify(node.data.config ?? {}, null, 2));
    setConfigError("");
    setFormState(syncFormFromNode);
  }, [node, syncFormFromNode]);

  if (!node) {
    return <div className="empty-state">Select a node on the canvas to edit its parameters.</div>;
  }

  const updateLabel = (value: string) => onUpdateNode(node.id, { label: value });

  const updateConfig = (partial: Partial<ConfigState>) => {
    const nextConfig = { ...formState, ...partial };
    setFormState(nextConfig);

    const configPayload: Record<string, unknown> = {};
    if (nextConfig.connection) configPayload.connection = nextConfig.connection;
    if (nextConfig.table) configPayload.table = nextConfig.table;
    if (nextConfig.columns) configPayload.columns = nextConfig.columns.split(",").map((item) => item.trim()).filter(Boolean);
    if (nextConfig.destination_table) configPayload.destination_table = nextConfig.destination_table;
    if (nextConfig.mode) configPayload.mode = nextConfig.mode;
    if (nextConfig.limit) configPayload.limit = Number(nextConfig.limit);
    
    // Handle routes structure for Router executor
    if (executorType === "router") {
        configPayload.routes = {
            true: nextConfig.routes_true,
            false: nextConfig.routes_false
        };
    }

    onUpdateNode(node.id, { config: configPayload });
  };

  const applyConfig = () => {
    try {
      const parsedConfig = JSON.parse(configText);
      onUpdateNode(node.id, { config: parsedConfig });
      onApplyConfiguration(node.id);
      setConfigError("");
      setConfigText(JSON.stringify(parsedConfig, null, 2));
      
      // Sync form state back from parsed JSON
      const routes = parsedConfig.routes ?? {};
      setFormState({
        connection: String(parsedConfig.connection ?? ""),
        table: String(parsedConfig.table ?? ""),
        columns: Array.isArray(parsedConfig.columns) ? parsedConfig.columns.join(", ") : String(parsedConfig.columns ?? ""),
        destination_table: String(parsedConfig.destination_table ?? ""),
        mode: String(parsedConfig.mode ?? "append"),
        limit: String(parsedConfig.limit ?? 10),
        routes_true: String(routes.true ?? ""),
        routes_false: String(routes.false ?? ""),
      });
    } catch {
      setConfigError("Config must be valid JSON.");
    }
  };

  return (
    <div className="properties-form">
      <label>
        Node Name
        <input value={node.data.label ?? ""} onChange={(event) => updateLabel(event.target.value)} />
      </label>
      <label>
        Executor Type
        <input value={executorType} disabled />
      </label>

      {executorType === "mysql_source" && (
        <>
          <label>
            Connection
            <select value={formState.connection} onChange={(event) => updateConfig({ connection: event.target.value })}>
              <option value="">Select connection</option>
              {connections.map((connection) => (
                <option key={connection.id} value={connection.id}>
                  {connection.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Source Table
            <input value={formState.table} onChange={(event) => updateConfig({ table: event.target.value })} placeholder="blood_donor_reg" />
          </label>
          <label>
            Columns
            <input value={formState.columns} onChange={(event) => updateConfig({ columns: event.target.value })} placeholder="id, name, updated_at" />
          </label>
        </>
      )}

      {executorType === "filter_transform" && (
        <label>
          Row Limit
          <input 
            type="number" 
            value={formState.limit} 
            onChange={(event) => updateConfig({ limit: event.target.value })} 
            placeholder="10" 
          />
          <small style={{color: '#9ca3af', display: 'block', marginTop: '4px'}}>
            Extract only the first N rows from the source.
          </small>
        </label>
      )}

      {executorType === "check_table_exists" && (
        <>
          <label>
            Connection
            <select value={formState.connection} onChange={(event) => updateConfig({ connection: event.target.value })}>
              <option value="">Select connection</option>
              {connections.map((connection) => (
                <option key={connection.id} value={connection.id}>
                  {connection.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Target Table
            <input value={formState.table} onChange={(event) => updateConfig({ table: event.target.value })} placeholder="fact_customers" />
          </label>
        </>
      )}

      {executorType === "create_table" && (
        <label>
          Destination Table
          <input
            value={formState.destination_table}
            onChange={(event) => updateConfig({ destination_table: event.target.value })}
            placeholder="warehouse.fact_customers"
          />
        </label>
      )}

      {executorType === "router" && (
        <>
          <label>
            Route on "True" (Executor ID or Label)
            <input 
              value={formState.routes_true} 
              onChange={(event) => updateConfig({ routes_true: event.target.value })} 
              placeholder="load_data" 
            />
            <small style={{color: '#9ca3af', display: 'block', marginTop: '4px'}}>
              Executed when Check Table Exists returns true.
            </small>
          </label>
          <label>
            Route on "False" (Executor ID or Label)
            <input 
              value={formState.routes_false} 
              onChange={(event) => updateConfig({ routes_false: event.target.value })} 
              placeholder="create_table" 
            />
            <small style={{color: '#9ca3af', display: 'block', marginTop: '4px'}}>
              Executed when Check Table Exists returns false.
            </small>
          </label>
        </>
      )}

      {executorType === "load_data" && (
        <>
          <label>
            Connection
            <select value={formState.connection} onChange={(event) => updateConfig({ connection: event.target.value })}>
              <option value="">Select connection</option>
              {connections.map((connection) => (
                <option key={connection.id} value={connection.id}>
                  {connection.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Destination Table
            <input
              value={formState.destination_table}
              onChange={(event) => updateConfig({ destination_table: event.target.value })}
              placeholder="warehouse.fact_customers"
            />
          </label>
          <label>
            Mode
            <input value={formState.mode} onChange={(event) => updateConfig({ mode: event.target.value })} placeholder="append" />
          </label>
        </>
      )}

      <label>
        Configuration JSON
        <textarea value={configText} onChange={(event) => setConfigText(event.target.value)} rows={10} />
      </label>
      {configError && <div className="error-text">{configError}</div>}
      <button type="button" className="secondary-button" onClick={applyConfig}>
        Apply Configuration
      </button>
    </div>
  );
}