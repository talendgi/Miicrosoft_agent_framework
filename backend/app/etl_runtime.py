from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

logger = logging.getLogger("WorkflowStudio")


@dataclass(frozen=True)
class ConnectionConfig:
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    account: Optional[str] = None
    warehouse: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None


class DatabaseConnector(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Any] = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def get_schema(self, table_name: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class MySQLConnector(DatabaseConnector):
    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
        self.connection = None
        self._connected = False
        self._simulate = not all([config.host, config.user, config.database])

    async def connect(self) -> bool:
        if self._connected:
            return True
        if self._simulate:
            self._connected = True
            return True

        import mysql.connector

        self.connection = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port or 3306,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
        )
        self._connected = True
        return True

    async def disconnect(self) -> None:
        if self.connection and self._connected:
            self.connection.close()
            self._connected = False

    async def execute_query(self, query: str, params: Optional[Any] = None) -> list[dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("MySQL connector is not connected.")
        if self._simulate:
            if query.lstrip().upper().startswith("SELECT"):
                return [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                ]
            return [{"rows_affected": 2}]
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if cursor.description is None:
                self.connection.commit()
                return [{"rows_affected": cursor.rowcount}]
            return cursor.fetchall()
        finally:
            cursor.close()

    async def get_schema(self, table_name: str) -> list[dict[str, Any]]:
        if self._simulate:
            return [
                {"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER", "IS_NULLABLE": "NO"},
                {"COLUMN_NAME": "NAME", "DATA_TYPE": "VARCHAR", "IS_NULLABLE": "YES"},
            ]
        query = """
            SELECT UPPER(COLUMN_NAME) AS COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        return await self.execute_query(query, (self.config.database, table_name))


class SnowflakeConnector(DatabaseConnector):
    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
        self.connection = None
        self._connected = False
        # Only simulate if critical fields are missing
        self._simulate = not all([config.account, config.user, config.database, config.schema, config.warehouse])

        logger.info(f"SnowflakeConnector initialized:")
        logger.info(f"  - Account: {config.account}")
        logger.info(f"  - User: {config.user}")
        logger.info(f"  - Database: {config.database}")
        logger.info(f"  - Schema: {config.schema}")
        logger.info(f"  - Warehouse: {config.warehouse}")
        logger.info(f"  - SIMULATION MODE: {self._simulate}")

        if self._simulate:
            missing = []
            if not config.account:
                missing.append("account")
            if not config.user:
                missing.append("user")
            if not config.database:
                missing.append("database")
            logger.warning(f"Missing required fields for real Snowflake connection: {missing}")
    async def connect(self) -> bool:
        if self._connected:
            return True
        if self._simulate:
            logger.warning("Running in SIMULATION MODE - no actual Snowflake connection")
            self._connected = True
            return True
        import snowflake.connector
        try:
            logger.info(f"Connecting to Snowflake account: {self.config.account}")
            self.connection = snowflake.connector.connect(
            account=self.config.account,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            schema=self.config.schema,
            warehouse=self.config.warehouse,
            role=self.config.role,
            )
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"Snowflake connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        if self.connection and self._connected:
            self.connection.close()
            self._connected = False

    async def execute_query(self, query: str, params: Optional[Any] = None) -> list[dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("Snowflake connector is not connected.")
        
        if self._simulate:
            logger.warning(f"⚠️ SIMULATED QUERY: {query[:100]}...")
            if "COUNT(*) AS CNT" in query.upper():
                return [{"CNT": 0}]
            if query.lstrip().upper().startswith("SELECT"):
                return [{"ID": 1, "NAME": "Alice"}]
            return [{"rows_affected": 2}]  # Fake success
        
        logger.info(f"🔵 Executing Snowflake query: {query}")
        if params:
            logger.debug(f"Parameters: {params}")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            
            if cursor.description is None:
                # This is an INSERT/UPDATE/DELETE
                rowcount = cursor.rowcount
                logger.info(f"✅ Query executed. Rows affected: {rowcount}")
                
                # CRITICAL: Commit the transaction
                self.connection.commit()
                logger.info(f"💾 Transaction committed")
                
                return [{"rows_affected": rowcount}]
            
            # SELECT query
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            logger.info(f"📊 SELECT returned {len(rows)} rows")
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            logger.error(f"Query was: {query}")
            self.connection.rollback()
            logger.info("🔄 Transaction rolled back")
            raise
        finally:
            cursor.close()

    async def get_schema(self, table_name: str) -> list[dict[str, Any]]:
        if self._simulate:
            return [
                {"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER", "IS_NULLABLE": "NO"},
                {"COLUMN_NAME": "NAME", "DATA_TYPE": "VARCHAR", "IS_NULLABLE": "YES"},
            ]
        query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        return await self.execute_query(query, (self.config.schema, table_name))

    async def table_exists(self, table_name: str) -> bool:
        if self._simulate:
            return table_name.lower().startswith("existing")
        query = """
            SELECT COUNT(*) AS CNT
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        rows = await self.execute_query(query, (self.config.schema, table_name.upper()))
        return bool(rows and rows[0].get("CNT", 0) > 0)

    async def create_table_if_not_exists(self, table_name: str, columns: list[dict[str, Any]]) -> None:
        if self._simulate:
            return
        column_sql = []
        for column in columns:
            name = column["COLUMN_NAME"].upper()
            dtype = column["DATA_TYPE"]
            nullable = column.get("IS_NULLABLE", "YES")
            null_sql = "NULL" if nullable == "YES" else "NOT NULL"
            column_sql.append(f'"{name}" {dtype} {null_sql}')

        statement = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_sql)})"
        await self.execute_query(statement)


class ExtractExecutor(Executor):
    def __init__(self, id: str, source_connector: DatabaseConnector, source_table: str) -> None:
        super().__init__(id=id)
        self.source_connector = source_connector
        self.source_table = source_table

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        await self.source_connector.connect()
        try:
            rows = await self.source_connector.execute_query(f"SELECT * FROM {self.source_table}")
            payload = {
                "records": rows,
                "source_table": self.source_table,
            }
            ctx.set_state("source_table", self.source_table)
            ctx.set_state("extracted_count", len(rows))
            await ctx.yield_output(payload)
            await ctx.send_message(payload)
            return payload
        finally:
            await self.source_connector.disconnect()


class TransformExecutor(Executor):
    def __init__(self, id: str) -> None:
        super().__init__(id=id)

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        records = input_data.get("records", [])
        for record in records:
            record["processed_at"] = datetime.utcnow().isoformat()
        ctx.set_state("transformed_count", len(records))
        payload = {
            "records": records,
            "source_table": input_data.get("source_table"),
            "record_count": len(records),
        }
        await ctx.yield_output(payload)
        await ctx.send_message(payload)
        return payload


class CheckTableExistsExecutor(Executor):
    def __init__(self, id: str, dest_connector: SnowflakeConnector, dest_table: str) -> None:
        super().__init__(id=id)
        self.dest_connector = dest_connector
        self.dest_table = dest_table

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        await self.dest_connector.connect()
        try:
            exists = await self.dest_connector.table_exists(self.dest_table)
            payload = {**input_data, "table_exists": exists}
            await ctx.yield_output(payload)
            await ctx.send_message(payload)
            return payload
        finally:
            await self.dest_connector.disconnect()


class CreateTableExecutor(Executor):
    def __init__(
        self,
        id: str,
        dest_connector: SnowflakeConnector,
        dest_table: str,
        source_connector: MySQLConnector,
        source_table: str,
    ) -> None:
        super().__init__(id=id)
        self.dest_connector = dest_connector
        self.dest_table = dest_table
        self.source_connector = source_connector
        self.source_table = source_table

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        logger.info(f"CreateTableExecutor: Creating table {self.dest_table}")
        
        # Get source schema from MySQL
        await self.source_connector.connect()
        try:
            source_schema = await self.source_connector.get_schema(self.source_table)
            logger.info(f"Source schema has {len(source_schema)} columns")
        finally:
            await self.source_connector.disconnect()

        # Add processed_at timestamp column
        source_schema.append(
            {"COLUMN_NAME": "PROCESSED_AT", "DATA_TYPE": "TIMESTAMP_NTZ", "IS_NULLABLE": "YES"}
        )

        # Create table in Snowflake
        await self.dest_connector.connect()
        try:
            await self.dest_connector.create_table_if_not_exists(self.dest_table, source_schema)
            logger.info(f"✅ Table {self.dest_table} created successfully")
            
            payload = {
                "table_created": True,
                "dest_table": self.dest_table,
                "columns": len(source_schema),
            }
            await ctx.yield_output(payload)
            await ctx.send_message(payload)
            return payload
        finally:
            await self.dest_connector.disconnect()


class RouterExecutor(Executor):
    """Routes to different executors based on conditions"""
    
    def __init__(self, id: str, routes: dict[str, str]) -> None:
        """
        routes: dict mapping condition values to executor IDs
        Example: {"true": "executor_1", "false": "executor_2"}
        """
        super().__init__(id=id)
        self.routes = routes

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        logger.info(f"RouterExecutor: Routing based on input: {input_data}")
        
        # Get the value to route on (from check_table_exists or other boolean executors)
        route_value = input_data.get("table_exists", input_data.get("value", False))
        route_key = str(route_value).lower()
        
        target_executor = self.routes.get(route_key)
        
        if not target_executor:
            logger.warning(f"No route found for value: {route_value}")
            target_executor = self.routes.get("default")
        
        logger.info(f"Routing to: {target_executor}")
        
        payload = {
            "routed_to": target_executor,
            "route_value": route_value,
            "input_data": input_data,
        }
        
        await ctx.yield_output(payload)
        await ctx.send_message(payload)
        return payload


class FilterTransformExecutor(Executor):
    """Filter records - take first N rows"""
    
    def __init__(self, id: str, limit: int = 10) -> None:
        super().__init__(id=id)
        self.limit = limit

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        logger.info(f"🔵 FilterTransformExecutor received input: {input_data}")
        logger.info(f"Input type: {type(input_data)}")
        logger.info(f"Input keys: {input_data.keys() if isinstance(input_data, dict) else 'N/A'}")
        
        records = input_data.get("records", [])
        logger.info(f"Records found: {len(records)}")
        
        # Also check if data is in a different structure
        if not records:
            # Try common alternative structures
            if isinstance(input_data, dict):
                for key, value in input_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        logger.info(f"Found data in key '{key}': {len(value)} items")
                        if isinstance(value[0], dict):
                            records = value
                            break
            
            # Check context state
            logger.info(f"Context state keys: {list(ctx.state.keys()) if hasattr(ctx, 'state') else 'N/A'}")
        
        original_count = len(records)
        filtered_records = records[:self.limit]
        filtered_count = len(filtered_records)
        
        logger.info(f"FilterTransform: {original_count} -> {filtered_count} records (limit: {self.limit})")
        
        payload = {
            "records": filtered_records,
            "source_table": input_data.get("source_table"),
            "original_count": original_count,
            "filtered_count": filtered_count,
            "limit": self.limit,
        }
        
        ctx.set_state("filtered_count", filtered_count)
        await ctx.yield_output(payload)
        await ctx.send_message(payload)
        return payload
    
class LoadExecutor(Executor):
    def __init__(self, id: str, dest_connector: DatabaseConnector, dest_table: str) -> None:
        super().__init__(id=id)
        self.dest_connector = dest_connector
        self.dest_table = dest_table

    @handler
    async def process(self, input_data: dict[str, Any], ctx: WorkflowContext[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
        records = input_data.get("records", [])
        
        logger.info(f"LoadExecutor started: {len(records)} records to load")
        logger.info(f"Destination table: {self.dest_table}")
        
        if not records:
            logger.warning("No records to load - skipping")
            empty_payload = {"status": "SKIPPED", "rows_loaded": 0}
            await ctx.yield_output(empty_payload)
            return empty_payload

        # Show first record for debugging
        logger.info(f"Sample record: {records[0]}")
        
        await self.dest_connector.connect()
        try:
            columns = [column.upper() for column in records[0].keys()]
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO {self.dest_table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            logger.info(f"INSERT Query: {insert_query}")
            logger.info(f"Columns: {columns}")
            
            rows_loaded = 0
            errors = []
            
            for i, record in enumerate(records):
                try:
                    normalized = {key.upper(): value for key, value in record.items()}
                    values = tuple(normalized.get(column) for column in columns)
                    
                    logger.debug(f"Inserting row {i+1}: {values}")
                    
                    result = await self.dest_connector.execute_query(insert_query, values)
                    logger.debug(f"Insert result: {result}")
                    
                    rows_loaded += 1
                    
                    if i == 0:  # Log only first row details
                        logger.info(f"First row inserted successfully")
                        
                except Exception as row_error:
                    logger.error(f"Failed to insert row {i+1}: {row_error}")
                    logger.error(f"Record data: {record}")
                    errors.append(f"Row {i+1}: {str(row_error)}")
            
            if errors:
                logger.error(f"Total errors: {len(errors)}")
                for err in errors[:5]:  # Show first 5 errors
                    logger.error(f"  - {err}")
            
            ctx.set_state("loaded_count", rows_loaded)
            payload = {
                "status": "COMPLETED" if not errors else "PARTIAL",
                "source_table": input_data.get("source_table"),
                "dest_table": self.dest_table,
                "rows_loaded": rows_loaded,
                "rows_failed": len(errors),
                "errors": errors[:10] if errors else None,  # Include first 10 errors
            }
            await ctx.yield_output(payload)
            await ctx.send_message(payload)
            return payload
            
        except Exception as e:
            logger.error(f"Error loading data into {self.dest_table}: {e}", exc_info=True)
            payload= {
                "status": "FAILED",
                "source_table": input_data.get("source_table"),
                "dest_table": self.dest_table,
                "rows_loaded": 0,
                "error": str(e),
            }
            await ctx.yield_output(payload)
            await ctx.send_message(payload)
            return payload
        finally:
            await self.dest_connector.disconnect()
            logger.info("Snowflake connection closed")


def create_etl_workflow(
    source_table: str,
    dest_table: str,
    mysql_config: ConnectionConfig,
    snowflake_config: ConnectionConfig,
    source_node_id: str = "extract_mysql",
    transform_node_id: str = "transform_data",
    load_node_id: str = "load_data",
    filter_limit: int = 10,  # New parameter
) -> Any:
    mysql_connector = MySQLConnector(mysql_config)
    snowflake_connector = SnowflakeConnector(snowflake_config)

    # Create executors
    extract_exec = ExtractExecutor(source_node_id, mysql_connector, source_table)
    filter_exec = FilterTransformExecutor(transform_node_id, limit=filter_limit)
    check_exec = CheckTableExistsExecutor("check_table_exists", snowflake_connector, dest_table)
    create_exec = CreateTableExecutor("create_table", snowflake_connector, dest_table, mysql_connector, source_table)
    load_exec = LoadExecutor(load_node_id, snowflake_connector, dest_table)
    
    # Router to branch based on table_exists
    router_exec = RouterExecutor("router", routes={
        "true": load_node_id,        # If table exists -> load
        "false": "create_table",     # If table doesn't exist -> create
    })

    builder = WorkflowBuilder(
        name="MySQL_to_Snowflake_ETL",
        description=f"ETL pipeline: {source_table} (MySQL) → {dest_table} (Snowflake)",
        start_executor=extract_exec,
        output_from=[load_exec],
        intermediate_output_from="all_other",
    )
    
    # Build the workflow graph
    builder.add_edge(extract_exec, filter_exec)
    builder.add_edge(filter_exec, check_exec)
    builder.add_edge(check_exec, router_exec)
    builder.add_edge(router_exec, load_exec, condition=lambda message: message.get("routed_to") == load_node_id)
    builder.add_edge(router_exec, create_exec, condition=lambda message: message.get("routed_to") == "create_table")
    builder.add_edge(create_exec, load_exec)
    
    return builder.build()
