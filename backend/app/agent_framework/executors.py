from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.agent_framework.context import WorkflowContext

def handler(func):
    """Decorator to mark a method as a workflow execution step."""
    func._is_handler = True
    return func

class Executor(ABC):
    executor_type: str

    @abstractmethod
    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MySqlSourceExecutor(Executor):
    executor_type = "mysql_source"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        table = node_data.get("table", "customers")
        columns = node_data.get("columns", ["id", "name", "updated_at"])
        return {
            "source_system": "mysql",
            "table": table,
            "columns": columns,
            "rows_sampled": 128,
            "fetched_at": datetime.utcnow().isoformat(),
        }


class FilterTransformExecutor(Executor):
    executor_type = "filter_transform"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        limit = node_data.get("limit", 10)
        upstream = context.values.get(node_data.get("input_key", "upstream"), {})
        return {
            "operation": "filter",
            "limit": limit,
            "input_snapshot": upstream,
        }


class CheckTableExistsExecutor(Executor):
    executor_type = "check_table_exists"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        table = node_data.get("table", "target_table")
        exists = table.lower().startswith("existing")
        return {"table": table, "exists": exists, "decision": "load" if exists else "create"}


class CreateTableExecutor(Executor):
    executor_type = "create_table"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        destination = node_data.get("destination_table", "warehouse.fact_table")
        return {
            "operation": "create_table",
            "destination_table": destination,
            "table_created": True,
        }


class RouterExecutor(Executor):
    executor_type = "router"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        routes = node_data.get("routes", {})
        return {
            "operation": "router",
            "routes": routes,
        }


class LoadDataExecutor(Executor):
    executor_type = "load_data"

    def execute(self, context: WorkflowContext, node_data: dict[str, Any]) -> dict[str, Any]:
        destination = node_data.get("destination_table", "warehouse.fact_table")
        mode = node_data.get("mode", "append")
        source_data = context.values.get(node_data.get("input_key", "upstream"), {})
        return {
            "destination_table": destination,
            "mode": mode,
            "records_loaded": source_data.get("rows_sampled", 128),
        }


class ExecutorRegistry:
    def __init__(self) -> None:
        self._executors = {
            MySqlSourceExecutor.executor_type: MySqlSourceExecutor(),
            FilterTransformExecutor.executor_type: FilterTransformExecutor(),
            CheckTableExistsExecutor.executor_type: CheckTableExistsExecutor(),
            CreateTableExecutor.executor_type: CreateTableExecutor(),
            RouterExecutor.executor_type: RouterExecutor(),
            LoadDataExecutor.executor_type: LoadDataExecutor(),
        }

    def list(self) -> list[dict[str, str]]:
        return [
            {"type": executor_type, "label": executor_type.replace("_", " ").title()}
            for executor_type in self._executors
        ]

    def get(self, executor_type: str) -> Executor:
        if executor_type not in self._executors:
            raise KeyError(f"Unsupported executor type: {executor_type}")
        return self._executors[executor_type]