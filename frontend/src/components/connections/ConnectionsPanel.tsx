import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, CheckCircle, XCircle, Loader2 } from "lucide-react";
import type { Connection } from "../../types";
import { api } from "../../api";

type Props = {
  connections: Connection[];
  onCreate: () => void;
  onEdit: (connection: Connection) => void;
  onRefresh: () => Promise<void>;
  modalConnection?: Connection | null;
  onModalClose?: () => void;
};

const blankConnection = (): Omit<Connection, "id"> => ({
  name: "",
  type: "mysql",
  host: "",
  port: 3306,
  database: "",
  username: "",
  password: "",
  schema_name: "",
  account: "",
  warehouse: "",
  role: "",
  ssl: false,
});

type TestResult = {
  status: "success" | "failed" | "simulation" | "unsupported";
  message: string;
  details?: any;
  result?: any;
};

export function ConnectionsPanel({ connections, onCreate, onEdit, onRefresh, modalConnection, onModalClose }: Props) {
  const [form, setForm] = useState<Omit<Connection, "id">>(blankConnection());
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  useEffect(() => {
    if (modalConnection === undefined) {
      return;
    }

    if (modalConnection === null) {
      setForm(blankConnection());
      return;
    }

    setForm({
      name: modalConnection.name,
      type: modalConnection.type,
      host: modalConnection.host,
      port: modalConnection.port,
      database: modalConnection.database,
      username: modalConnection.username,
      password: modalConnection.password,
      schema_name: modalConnection.schema_name ?? "",
      account: modalConnection.account ?? "",
      warehouse: modalConnection.warehouse ?? "",
      role: modalConnection.role ?? "",
      ssl: modalConnection.ssl,
    });
  }, [modalConnection]);

  const persist = async () => {
    if (modalConnection && modalConnection !== null) {
      await api.connections.update(modalConnection.id, form);
    } else {
      await api.connections.create(form);
    }
    await onRefresh();
    onModalClose?.();
  };

  const testConnection = async (connectionId: string) => {
    setTestingId(connectionId);
    setTestResult(null);
    
    try {
      // const result = await api.connections.test(connectionId);
      const result = await api.connections.test(connectionId) as TestResult;
      setTestResult(result);
    } catch (error) {
      setTestResult({
        status: "failed",
        message: error instanceof Error ? error.message : "Test failed",
      });
    } finally {
      setTestingId(null);
    }
  };

  const isSnowflake = form.type === "snowflake";

  return (
    <section className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Connection Manager</h2>
          <p>Create and maintain source, warehouse, and API connections.</p>
        </div>
        {modalConnection === undefined && (
          <button type="button" className="primary-button" onClick={onCreate}>
            <Plus size={16} />
            Add Connection
          </button>
        )}
      </div>

      {modalConnection === undefined ? (
        <div className="panel-table">
          {connections.map((connection) => (
            <div className="table-row" key={connection.id}>
              <div>
                <strong>{connection.name}</strong>
                <div className="muted">
                  {connection.type} - {connection.host || connection.account || "N/A"}
                  {connection.port ? `:${connection.port}` : ""}
                </div>
              </div>
              <div className="row-actions">
                <button
                  type="button"
                  className="icon-button test-btn"
                  onClick={() => testConnection(connection.id)}
                  disabled={testingId === connection.id}
                  title="Test connection"
                >
                  {testingId === connection.id ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <CheckCircle size={14} />
                  )}
                </button>
                <button type="button" className="icon-button" onClick={() => onEdit(connection)}>
                  <Pencil size={14} />
                </button>
                <button
                  type="button"
                  className="icon-button danger"
                  onClick={async () => {
                    await api.connections.remove(connection.id);
                    await onRefresh();
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
          
          {testResult && (
            <div className={`test-result ${testResult.status}`}>
              <div className="test-result-header">
                {testResult.status === "success" && <CheckCircle size={20} />}
                {testResult.status === "failed" && <XCircle size={20} />}
                {testResult.status === "simulation" && <Loader2 size={20} />}
                <strong>
                  {testResult.status === "success" && "Connection Successful!"}
                  {testResult.status === "failed" && "Connection Failed"}
                  {testResult.status === "simulation" && "Simulation Mode"}
                </strong>
              </div>
              <p>{testResult.message}</p>
              {testResult.details && (
                <pre className="test-details">{JSON.stringify(testResult.details, null, 2)}</pre>
              )}
              <button className="close-test" onClick={() => setTestResult(null)}>
                Close
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="modal-form">
          <div className="grid-form">
            <label>
              Name
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
            </label>
            <label>
              Type
              <select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as Connection["type"] })}>
                <option value="mysql">MySQL</option>
                <option value="postgres">Postgres</option>
                <option value="snowflake">Snowflake</option>
                <option value="sqlserver">SQL Server</option>
                <option value="api">API</option>
              </select>
            </label>

            {isSnowflake && (
              <>
                <label>
                  Account
                  <input
                    value={form.account ?? ""}
                    onChange={(event) => setForm({ ...form, account: event.target.value })}
                    placeholder="xy12345.us-east-1"
                  />
                </label>
                <label>
                  Warehouse
                  <input
                    value={form.warehouse ?? ""}
                    onChange={(event) => setForm({ ...form, warehouse: event.target.value })}
                    placeholder="COMPUTE_WH"
                  />
                </label>
                <label>
                  Role (optional)
                  <input
                    value={form.role ?? ""}
                    onChange={(event) => setForm({ ...form, role: event.target.value })}
                    placeholder="ACCOUNTADMIN"
                  />
                </label>
              </>
            )}

            {!isSnowflake && (
              <>
                <label>
                  Host
                  <input value={form.host} onChange={(event) => setForm({ ...form, host: event.target.value })} />
                </label>
                <label>
                  Port
                  <input type="number" value={form.port} onChange={(event) => setForm({ ...form, port: Number(event.target.value) })} />
                </label>
              </>
            )}

            <label>
              Database
              <input value={form.database} onChange={(event) => setForm({ ...form, database: event.target.value })} />
            </label>
            <label>
              Username
              <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
            </label>
            <label>
              Password
              <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            </label>
            <label>
              Schema
              <input value={form.schema_name ?? ""} onChange={(event) => setForm({ ...form, schema_name: event.target.value })} />
            </label>
          </div>

          {isSnowflake && (
            <div className="info-banner">
              <strong>Snowflake Connection Tip:</strong>
              <p>
                The <em>Account</em> field should include the region (e.g., <code>xy12345.us-east-1</code>).
                The <em>Warehouse</em> is required for query execution. Without these, the connector will run in simulation mode.
              </p>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={onModalClose}>
              Cancel
            </button>
            <button type="button" className="primary-button" onClick={persist}>
              Save Connection
            </button>
          </div>
        </div>
      )}
    </section>
  );
}