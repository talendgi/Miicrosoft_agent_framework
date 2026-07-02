export type ExecutorType = "mysql_source" | "transform_data" | "check_table_exists" | "load_data";

export type StudioNodeData = {
  label: string;
  executorType: ExecutorType;
  executor_type?: ExecutorType;
  description: string;
  config: Record<string, string | number | boolean | string[]>;
};

export type Connection = {
  id: string;
  name: string;
  type: "mysql" | "postgres" | "snowflake" | "sqlserver" | "api";
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  schema_name?: string | null;
  account?: string;     
  warehouse?: string;    
  role?: string;        
  ssl: boolean;
};

export type Pipeline = {
  id: string;
  name: string;
  description: string;
  nodes: any[];
  edges: any[];
  connection_id?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type ExecutionRecord = {
  id: string;
  pipeline_id: string;
  pipeline_name: string;
  status: "success" | "failed" | "running";
  started_at: string;
  finished_at?: string | null;
  logs?: string[];
  node_results: Array<{
    node_id: string;
    node_label: string;
    executor_type: string;
    status: "success" | "failed";
    started_at: string;
    finished_at: string;
    output: Record<string, unknown>;
    logs?: string[];
    error?: string | null;
  }>;
};

export type ExecutorCatalogItem = {
  type: ExecutorType;
  label: string;
  category: string;
  description: string;
};
