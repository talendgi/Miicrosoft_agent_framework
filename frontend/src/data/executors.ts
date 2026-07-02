import type { ExecutorCatalogItem, ExecutorType, StudioNodeData } from "../types";

export const executorCatalog = [
  {
    type: "mysql_source",
    label: "Extract from MySQL",
    category: "Source",
    description: "Read rows from a source MySQL table.",
    icon: "database",
    defaultConfig: {
      table: "",
      columns: [],
    },
  },
  {
    type: "filter_transform",
    label: "Filter Rows",
    category: "Transform",
    description: "Filter records - take first N rows.",
    icon: "filter",
    defaultConfig: {
      limit: 10,
    },
  },
  {
    type: "check_table_exists",
    label: "Check Table Exists",
    category: "Control",
    description: "Check if destination table exists in Snowflake.",
    icon: "search",
    defaultConfig: {
      table: "",
    },
  },
  {
    type: "create_table",
    label: "Create Table",
    category: "Load",
    description: "Create destination table in Snowflake.",
    icon: "table",
    defaultConfig: {
      destination_table: "",
    },
  },
  {
    type: "router",
    label: "Router",
    category: "Control",
    description: "Route to different executors based on conditions.",
    icon: "git-branch",
    defaultConfig: {
      routes: {
        true: "",
        false: "",
      },
    },
  },
  {
    type: "load_data",
    label: "Load Data",
    category: "Load",
    description: "Persist transformed data to a warehouse target.",
    icon: "upload",
    defaultConfig: {
      destination_table: "",
      mode: "append",
    },
  },
];

export const defaultNodeConfig = (type: ExecutorType): StudioNodeData["config"] => {
  switch (type) {
    case "mysql_source":
      return { connection: "", table: "customers", columns: ["id", "name"] };
    case "transform_data":
      return { rules: "trim,normalize,cast", output_shape: "normalized" };
    case "check_table_exists":
      return { connection: "", table: "existing_target" };
    case "load_data":
      return { connection: "", destination_table: "warehouse.fact_customers", mode: "append" };
  }
};

export const buildNodeData = (type: ExecutorType, label: string): StudioNodeData => ({
  label,
  executorType: type,
  executor_type: type,
  description: executorCatalog.find((item) => item.type === type)?.description ?? "",
  config: defaultNodeConfig(type),
});
