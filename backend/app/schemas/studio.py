from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Connection(BaseRecord):
    name: str
    type: Literal["mysql", "postgres", "snowflake", "sqlserver", "api"]
    host: str
    port: int
    database: str
    username: str
    password: str
    schema_name: str | None = None
    account: str | None = None      #  for Snowflake
    warehouse: str | None = None    #  for Snowflake
    role: str | None = None
    ssl: bool = False


class NodeDefinition(BaseModel):
    id: str
    type: str
    label: str
    position: dict[str, float]
    data: dict[str, Any] = Field(default_factory=dict)


class EdgeDefinition(BaseModel):
    id: str
    source: str
    target: str
    source_handle: str | None = None
    target_handle: str | None = None


class Pipeline(BaseRecord):
    name: str
    description: str = ""
    nodes: list[NodeDefinition] = Field(default_factory=list)
    edges: list[EdgeDefinition] = Field(default_factory=list)
    connection_id: str | None = None


class NodeExecutionResult(BaseModel):
    node_id: str
    node_label: str
    executor_type: str
    status: Literal["success", "failed"]
    started_at: datetime
    finished_at: datetime
    output: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    error: str | None = None


class ExecutionRecord(BaseRecord):
    pipeline_id: str
    pipeline_name: str
    status: Literal["success", "failed", "running"]
    started_at: datetime
    finished_at: datetime | None = None
    node_results: list[NodeExecutionResult] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)


class PipelineRunResponse(BaseModel):
    execution: ExecutionRecord


class SavePipelineRequest(BaseModel):
    name: str
    description: str = ""
    nodes: list[NodeDefinition] = Field(default_factory=list)
    edges: list[EdgeDefinition] = Field(default_factory=list)
    connection_id: str | None = None


class SaveConnectionRequest(BaseModel):
    name: str
    type: Literal["mysql", "postgres", "snowflake", "sqlserver", "api"]
    host: str
    port: int
    database: str
    username: str
    password: str
    schema_name: str | None = None
    account: str | None = None     
    warehouse: str | None = None   
    role: str | None = None      
    ssl: bool = False
