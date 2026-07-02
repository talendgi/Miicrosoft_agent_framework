from __future__ import annotations
import logging
import asyncio
import inspect
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_framework import WorkflowRunResult

logger = logging.getLogger("PipelineService")

# from app.etl_runtime import ConnectionConfig, create_etl_workflow
from app.etl_runtime import (
    ConnectionConfig,
    create_etl_workflow,
    WorkflowBuilder,
    MySQLConnector,
    SnowflakeConnector,
    ExtractExecutor,
    FilterTransformExecutor,
    TransformExecutor,
    CheckTableExistsExecutor,
    CreateTableExecutor,
    RouterExecutor,
    LoadExecutor,
)

from app.schemas.studio import (
    Connection,
    ExecutionRecord,
    NodeExecutionResult,
    Pipeline,
    SaveConnectionRequest,
    SavePipelineRequest,
)
from app.storage.json_store import JsonStore


class PipelineService:
    def __init__(self, store_path: Path | None = None) -> None:
        root = store_path or Path(__file__).resolve().parents[2] / "data" / "studio.json"
        self._store = JsonStore(root)

    def list_connections(self) -> list[Connection]:
        return [Connection.model_validate(item) for item in self._store.read().get("connections", [])]

    def save_connection(self, payload: SaveConnectionRequest, connection_id: str | None = None) -> Connection:
        data = self._store.read()
        connections = data.get("connections", [])
        existing = next((item for item in connections if item["id"] == connection_id), None) if connection_id else None
        if connection_id:
            connections = [item for item in connections if item["id"] != connection_id]
        payload_data = payload.model_dump()
        if connection_id or existing:
            payload_data["id"] = connection_id or existing["id"]
            payload_data["created_at"] = existing["created_at"] if existing else datetime.utcnow()
        payload_data["updated_at"] = datetime.utcnow()
        connection = Connection.model_validate(payload_data)
        connections.append(connection.model_dump(mode="json"))
        data["connections"] = connections
        self._store.write(data)
        return connection

    def delete_connection(self, connection_id: str) -> None:
        data = self._store.read()
        data["connections"] = [item for item in data.get("connections", []) if item["id"] != connection_id]
        self._store.write(data)

    def list_pipelines(self) -> list[Pipeline]:
        return [Pipeline.model_validate(item) for item in self._store.read().get("pipelines", [])]

    def save_pipeline(self, payload: SavePipelineRequest, pipeline_id: str | None = None) -> Pipeline:
        data = self._store.read()
        pipelines = data.get("pipelines", [])
        existing = next((item for item in pipelines if item["id"] == pipeline_id), None) if pipeline_id else None
        if pipeline_id:
            pipelines = [item for item in pipelines if item["id"] != pipeline_id]
        payload_data = payload.model_dump()
        if pipeline_id or existing:
            payload_data["id"] = pipeline_id or existing["id"]
            payload_data["created_at"] = existing["created_at"] if existing else datetime.utcnow()
        payload_data["updated_at"] = datetime.utcnow()
        pipeline = Pipeline.model_validate(payload_data)
        pipelines.append(pipeline.model_dump(mode="json"))
        data["pipelines"] = pipelines
        self._store.write(data)
        return pipeline

    def delete_pipeline(self, pipeline_id: str) -> None:
        data = self._store.read()
        data["pipelines"] = [item for item in data.get("pipelines", []) if item["id"] != pipeline_id]
        self._store.write(data)

    def run_pipeline(self, pipeline_id: str) -> ExecutionRecord:
        data = self._store.read()
        pipeline_data = next((item for item in data.get("pipelines", []) if item["id"] == pipeline_id), None)
        if pipeline_data is None:
            raise ValueError("Pipeline not found.")

        pipeline = Pipeline.model_validate(pipeline_data)
        started_at = datetime.utcnow()
        logs: list[str] = [
            f"[{started_at.isoformat()}] Pipeline started: {pipeline.name}",
            f"[{started_at.isoformat()}] Nodes: {len(pipeline.nodes)}, Edges: {len(pipeline.edges)}",
        ]
        execution = ExecutionRecord(
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name,
            status="running",
            started_at=started_at,
            logs=logs,
        )

        try:
            workflow = self._build_workflow(pipeline)
            logs.append(f"[{datetime.utcnow().isoformat()}] Workflow builder created successfully")
            if inspect.iscoroutinefunction(workflow.run):
                run_result = asyncio.run(workflow.run({"pipeline_id": pipeline.id, "trigger": "ui"}))
            else:
                run_result = workflow.run({"pipeline_id": pipeline.id, "trigger": "ui"})

            if not isinstance(run_result, WorkflowRunResult):
                raise TypeError("Unexpected workflow result type.")

            outputs_by_executor: dict[str, Any] = {}
            node_logs: dict[str, list[str]] = {node.id: [] for node in pipeline.nodes}
            
            for event in run_result:
                event_type = getattr(event, "type", None)
                executor_id = getattr(event, "executor_id", None)
                event_data = getattr(event, "data", None)
                summary = self._summarize(event_data)
                
                if executor_id:
                    node_logs.setdefault(executor_id, []).append(f"{event_type}: {summary}")
                
                logs.append(
                    f"[{datetime.utcnow().isoformat()}] event={event_type} executor={executor_id or 'workflow'} payload={summary}"
                )
                
                # Capture outputs - map executor_id to outputs
                if event_type in {"output", "intermediate", "data"} and executor_id:
                    outputs_by_executor[executor_id] = event_data
                    logs.append(f"[DEBUG] Captured output for executor={executor_id}")

            # Debug logging
            logs.append(f"[DEBUG] outputs_by_executor keys: {list(outputs_by_executor.keys())}")
            logs.append(f"[DEBUG] node IDs: {[node.id for node in pipeline.nodes]}")
            
            # Create node results with proper mapping
            execution.node_results = []
            for node in pipeline.nodes:
                # Try to find output by node.id first
                output = outputs_by_executor.get(node.id, {})
                
                # Fallback: try to find by executor type or partial match
                if not output:
                    for exec_id, exec_output in outputs_by_executor.items():
                        # Match if executor_id contains node.type or vice versa
                        if node.type in exec_id or exec_id in node.type:
                            output = exec_output
                            logs.append(f"[DEBUG] Matched node {node.id} ({node.type}) to executor {exec_id}")
                            break
                
                execution.node_results.append(
                    NodeExecutionResult(
                        node_id=node.id,
                        node_label=node.label,
                        executor_type=node.type,
                        status="success",
                        started_at=started_at,
                        finished_at=datetime.utcnow(),
                        output=output,
                        logs=node_logs.get(node.id, []),
                    )
                )
                
            execution.status = "success"
            logs.append(f"[{datetime.utcnow().isoformat()}] Pipeline completed successfully")
            
        except Exception as exc:
            execution.status = "failed"
            error_message = f"{type(exc).__name__}: {exc}"
            logs.append(f"[{datetime.utcnow().isoformat()}] Pipeline failed: {error_message}")
            logs.append(traceback.format_exc())
            execution.node_results = [
                NodeExecutionResult(
                    node_id=node.id,
                    node_label=node.label,
                    executor_type=node.type,
                    status="failed",
                    started_at=started_at,
                    finished_at=datetime.utcnow(),
                    output={},
                    logs=[error_message],
                    error=str(exc),
                )
                for node in pipeline.nodes
            ]
        finally:
            execution.finished_at = datetime.utcnow()
            execution.logs = logs
            data.setdefault("executions", [])
            data["executions"].append(execution.model_dump(mode="json"))
            self._store.write(data)

        return execution

    def _build_workflow(self, pipeline: Pipeline):
        """Dynamically build workflow based on canvas nodes and edges"""
        connection_lookup = {connection.id: connection for connection in self.list_connections()}
        default_connection = connection_lookup.get(pipeline.connection_id) if pipeline.connection_id else None

        # Build executors from nodes
        executors = {}
        node_executors = {}
        
        # Find MySQL and Snowflake connections
        mysql_connection = None
        snowflake_connection = None
        
        for node in pipeline.nodes:
            node_config = self._node_config(node)
            
            if node.type == "mysql_source":
                conn_id = node_config.get("connection")
                if conn_id and conn_id in connection_lookup:
                    mysql_connection = connection_lookup[conn_id]
                elif default_connection:
                    mysql_connection = default_connection
                    
            elif node.type in ["load_data", "check_table_exists", "create_table"]:
                conn_id = node_config.get("connection")
                if conn_id and conn_id in connection_lookup:
                    snowflake_connection = connection_lookup[conn_id]
                elif default_connection:
                    snowflake_connection = default_connection
        
        # Convert to ConnectionConfig
        mysql_config = self._to_connection_config(mysql_connection) if mysql_connection else ConnectionConfig()
        snowflake_config = self._to_connection_config(snowflake_connection) if snowflake_connection else ConnectionConfig()
        
        logger.info(f"MySQL Config: host={mysql_config.host}, user={mysql_config.user}, database={mysql_config.database}")
        logger.info(f"Snowflake Config: account={snowflake_config.account}, warehouse={snowflake_config.warehouse}")
        
        # Create connectors
        mysql_connector = MySQLConnector(mysql_config)
        snowflake_connector = SnowflakeConnector(snowflake_config)
        
        # Create executors from nodes
        for node in pipeline.nodes:
            node_config = self._node_config(node)
            
            if node.type == "mysql_source":
                table = node_config.get("table", "customers")
                executors[node.id] = ExtractExecutor(node.id, mysql_connector, table)
                
            elif node.type == "filter_transform":
                limit = node_config.get("limit", 10)
                executors[node.id] = FilterTransformExecutor(node.id, limit=limit)
                
            elif node.type == "transform_data":
                executors[node.id] = TransformExecutor(node.id)
                
            elif node.type == "check_table_exists":
                table = node_config.get("table", "target_table")
                executors[node.id] = CheckTableExistsExecutor(node.id, snowflake_connector, table)
                
            elif node.type == "create_table":
                dest_table = node_config.get("destination_table", "warehouse.table")
                source_table = node_config.get("source_table", table)  # Get from node config
                source_db = node_config.get("source_db", "mysql")
                target_db = node_config.get("target_db", "snowflake")
                
                executors[node.id] = CreateTableExecutor(
                    node.id, 
                    snowflake_connector, 
                    dest_table,
                    mysql_connector,  # Pass the connector
                    source_table,
                    source_db=source_db,
                    target_db=target_db,
                )
                
            elif node.type == "router":
                routes = node_config.get("routes", {})
                executors[node.id] = RouterExecutor(node.id, routes)
                
            elif node.type == "load_data":
                dest_table = node_config.get("destination_table", "warehouse.table")
                executors[node.id] = LoadExecutor(node.id, snowflake_connector, dest_table)
            
            node_executors[node.id] = executors[node.id]
        
        # Build workflow from edges (rest of the code stays the same...)
        if not executors:
            raise ValueError("No executors found in pipeline")
        
        # Find start executor
        target_nodes = {edge.target for edge in pipeline.edges}
        start_executor = next(
            (exec for node_id, exec in executors.items() if node_id not in target_nodes),
            list(executors.values())[0]
        )
        
        builder = WorkflowBuilder(
            name=pipeline.name,
            description=pipeline.description or "Dynamic ETL workflow",
            start_executor=start_executor,
            output_from=[executors.get(edge.target) for edge in pipeline.edges if edge.target in executors],
            intermediate_output_from="all_other",
        )
        
        # Add edges
        for edge in pipeline.edges:
            source_exec = executors.get(edge.source)
            target_exec = executors.get(edge.target)
            
            if source_exec and target_exec:
                condition = None
                if hasattr(edge, 'data') and edge.data:
                    condition_data = edge.data.get('condition')
                    if condition_data:
                        if condition_data == "table_exists_true":
                            condition = lambda msg: msg.get("table_exists", False)
                        elif condition_data == "table_exists_false":
                            condition = lambda msg: not msg.get("table_exists", False)
                
                builder.add_edge(source_exec, target_exec, condition=condition)
        
        return builder.build()

    def _select_connection(
        self,
        connection_lookup: dict[str, Connection],
        pipeline: Pipeline,
        executor_type: str,
        fallback: Connection | None,
    ) -> Connection | None:
        for node in pipeline.nodes:
            if node.type == executor_type:
                node_connection_id = self._node_config(node).get("connection")
                if node_connection_id and node_connection_id in connection_lookup:
                    return connection_lookup[node_connection_id]
        return fallback

    def _node_config(self, node) -> dict[str, Any]:
        config = node.data.get("config")
        return config if isinstance(config, dict) else {}

    def _summarize(self, value: Any) -> str:
        try:
            if isinstance(value, dict):
                # For extract/transform events, show record counts
                if "records" in value:
                    record_count = len(value.get("records", []))
                    table_name = value.get("source_table", "unknown")
                    return f"table={table_name} records={record_count}"
                
                # For load events, show load summary
                if "rows_loaded" in value:
                    return f"status={value.get('status')} rows_loaded={value.get('rows_loaded')} dest_table={value.get('dest_table')}"
                
                # For check events
                if "table_exists" in value:
                    return f"table_exists={value.get('table_exists')}"
                    
                return json.dumps({k: v for k, v in value.items() if k not in ["records"]}, default=str)[:200]
            
            if isinstance(value, list):
                return f"list[{len(value)} items]"
                
            return str(value)[:200]
        except Exception:
            return repr(value)[:200]
    def _to_connection_config(self, connection: Connection | None) -> ConnectionConfig:
        if connection is None:
            return ConnectionConfig()

        return ConnectionConfig(
            host=connection.host,
            port=connection.port,
            user=connection.username,
            password=connection.password,
            database=connection.database,
            schema=connection.schema_name,
            account=getattr(connection, "account", None),
            warehouse=getattr(connection, "warehouse", None),
            role=getattr(connection, "role", None),
        )
    def delete_execution(self, execution_id: str) -> None:
        """Delete a specific execution log"""
        data = self._store.read()
        data["executions"] = [
            item for item in data.get("executions", []) 
            if item["id"] != execution_id
        ]
        self._store.write(data)

    def clear_all_executions(self) -> None:
        """Clear all execution logs"""
        data = self._store.read()
        data["executions"] = []
        self._store.write(data)
    def list_executions(self) -> list[ExecutionRecord]:
        return [ExecutionRecord.model_validate(item) for item in self._store.read().get("executions", [])]

    def executor_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "mysql_source",
                "label": "Extract from MySQL",
                "category": "Source",
                "description": "Read rows from a source MySQL table.",
            },
            {
                "type": "transform_data",
                "label": "Transform Data",
                "category": "Transform",
                "description": "Clean, reshape, and enrich incoming data.",
            },
            {
                "type": "check_table_exists",
                "label": "Check Table Exists",
                "category": "Control",
                "description": "Branch based on whether a destination table is present.",
            },
            {
                "type": "load_data",
                "label": "Load Data",
                "category": "Load",
                "description": "Persist transformed data to a warehouse target.",
            },
        ]
