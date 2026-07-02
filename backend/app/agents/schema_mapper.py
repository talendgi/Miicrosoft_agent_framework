from typing import Any, Optional
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class SchemaMapperAgent(BaseAgent):
    """
    Agent that generates CREATE TABLE DDL based on source and target database types.
    Supports: MySQL, PostgreSQL, SQL Server -> Snowflake, BigQuery, Redshift, PostgreSQL
    """
    
    def __init__(self, model: str = "local"):
        super().__init__(model)
        
        # Comprehensive type mapping matrix
        # Format: {source_db: {source_type: {target_db: target_type}}}
        self.type_mapping_matrix = {
            'mysql': {
                'int': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'integer': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'tinyint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'SMALLINT', 'postgresql': 'SMALLINT'},
                'smallint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'SMALLINT', 'postgresql': 'SMALLINT'},
                'mediumint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'bigint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'BIGINT', 'postgresql': 'BIGINT'},
                'float': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'REAL', 'postgresql': 'REAL'},
                'double': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'DOUBLE PRECISION', 'postgresql': 'DOUBLE PRECISION'},
                'decimal': {'snowflake': 'NUMBER', 'bigquery': 'NUMERIC', 'redshift': 'DECIMAL', 'postgresql': 'NUMERIC'},
                'numeric': {'snowflake': 'NUMBER', 'bigquery': 'NUMERIC', 'redshift': 'DECIMAL', 'postgresql': 'NUMERIC'},
                'varchar': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'char': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'CHAR', 'postgresql': 'CHAR'},
                'text': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'tinytext': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(256)', 'postgresql': 'TEXT'},
                'mediumtext': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'longtext': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'date': {'snowflake': 'DATE', 'bigquery': 'DATE', 'redshift': 'DATE', 'postgresql': 'DATE'},
                'datetime': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'DATETIME', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'timestamp': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'TIMESTAMP', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'time': {'snowflake': 'TIME', 'bigquery': 'TIME', 'redshift': 'TIME', 'postgresql': 'TIME'},
                'year': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'bit': {'snowflake': 'BOOLEAN', 'bigquery': 'BOOL', 'redshift': 'BOOLEAN', 'postgresql': 'BOOLEAN'},
                'boolean': {'snowflake': 'BOOLEAN', 'bigquery': 'BOOL', 'redshift': 'BOOLEAN', 'postgresql': 'BOOLEAN'},
                'enum': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'set': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'json': {'snowflake': 'VARIANT', 'bigquery': 'JSON', 'redshift': 'SUPER', 'postgresql': 'JSONB'},
                'blob': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'tinyblob': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'mediumblob': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'longblob': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'binary': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'varbinary': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
            },
            'postgresql': {
                'integer': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'smallint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'SMALLINT', 'postgresql': 'SMALLINT'},
                'bigint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'BIGINT', 'postgresql': 'BIGINT'},
                'real': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'REAL', 'postgresql': 'REAL'},
                'double precision': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'DOUBLE PRECISION', 'postgresql': 'DOUBLE PRECISION'},
                'numeric': {'snowflake': 'NUMBER', 'bigquery': 'NUMERIC', 'redshift': 'DECIMAL', 'postgresql': 'NUMERIC'},
                'varchar': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'char': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'CHAR', 'postgresql': 'CHAR'},
                'text': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'date': {'snowflake': 'DATE', 'bigquery': 'DATE', 'redshift': 'DATE', 'postgresql': 'DATE'},
                'timestamp': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'TIMESTAMP', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'time': {'snowflake': 'TIME', 'bigquery': 'TIME', 'redshift': 'TIME', 'postgresql': 'TIME'},
                'boolean': {'snowflake': 'BOOLEAN', 'bigquery': 'BOOL', 'redshift': 'BOOLEAN', 'postgresql': 'BOOLEAN'},
                'jsonb': {'snowflake': 'VARIANT', 'bigquery': 'JSON', 'redshift': 'SUPER', 'postgresql': 'JSONB'},
                'bytea': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
            },
            'sqlserver': {
                'int': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'INTEGER', 'postgresql': 'INTEGER'},
                'bigint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'BIGINT', 'postgresql': 'BIGINT'},
                'smallint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'SMALLINT', 'postgresql': 'SMALLINT'},
                'tinyint': {'snowflake': 'NUMBER', 'bigquery': 'INT64', 'redshift': 'SMALLINT', 'postgresql': 'SMALLINT'},
                'float': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'REAL', 'postgresql': 'REAL'},
                'real': {'snowflake': 'FLOAT', 'bigquery': 'FLOAT64', 'redshift': 'REAL', 'postgresql': 'REAL'},
                'decimal': {'snowflake': 'NUMBER', 'bigquery': 'NUMERIC', 'redshift': 'DECIMAL', 'postgresql': 'NUMERIC'},
                'numeric': {'snowflake': 'NUMBER', 'bigquery': 'NUMERIC', 'redshift': 'DECIMAL', 'postgresql': 'NUMERIC'},
                'varchar': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'nvarchar': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'VARCHAR'},
                'char': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'CHAR', 'postgresql': 'CHAR'},
                'nchar': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'CHAR', 'postgresql': 'CHAR'},
                'text': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'ntext': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'TEXT'},
                'date': {'snowflake': 'DATE', 'bigquery': 'DATE', 'redshift': 'DATE', 'postgresql': 'DATE'},
                'datetime': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'DATETIME', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'datetime2': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'DATETIME', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'smalldatetime': {'snowflake': 'TIMESTAMP_NTZ', 'bigquery': 'DATETIME', 'redshift': 'TIMESTAMP', 'postgresql': 'TIMESTAMP'},
                'time': {'snowflake': 'TIME', 'bigquery': 'TIME', 'redshift': 'TIME', 'postgresql': 'TIME'},
                'bit': {'snowflake': 'BOOLEAN', 'bigquery': 'BOOL', 'redshift': 'BOOLEAN', 'postgresql': 'BOOLEAN'},
                'uniqueidentifier': {'snowflake': 'VARCHAR', 'bigquery': 'STRING', 'redshift': 'VARCHAR', 'postgresql': 'UUID'},
                'xml': {'snowflake': 'TEXT', 'bigquery': 'STRING', 'redshift': 'VARCHAR(MAX)', 'postgresql': 'XML'},
                'varbinary': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
                'binary': {'snowflake': 'BINARY', 'bigquery': 'BYTES', 'redshift': 'VARBYTE', 'postgresql': 'BYTEA'},
            },
        }
        
        # DDL syntax templates for different target databases
        self.ddl_templates = {
            'snowflake': {
                'table_start': 'CREATE TABLE IF NOT EXISTS {table_name} (',
                'column_format': '    "{column_name}" {data_type} {nullable}',
                'table_end': ')',
                'comment_syntax': 'COMMENT = \'{comment}\'',
                'default_timestamp': 'DEFAULT CURRENT_TIMESTAMP()',
            },
            'bigquery': {
                'table_start': 'CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.{table_name}` (',
                'column_format': '  {column_name} {data_type} {nullable}',
                'table_end': ')',
                'comment_syntax': 'OPTIONS(description="{comment}")',
                'default_timestamp': 'DEFAULT CURRENT_TIMESTAMP()',
            },
            'redshift': {
                'table_start': 'CREATE TABLE IF NOT EXISTS {table_name} (',
                'column_format': '    {column_name} {data_type} {nullable}',
                'table_end': ')',
                'comment_syntax': None,  # Redshift doesn't support table comments in CREATE TABLE
                'default_timestamp': 'DEFAULT GETDATE()',
            },
            'postgresql': {
                'table_start': 'CREATE TABLE IF NOT EXISTS {table_name} (',
                'column_format': '    {column_name} {data_type} {nullable}',
                'table_end': ')',
                'comment_syntax': None,  # Comments are separate statements in PostgreSQL
                'default_timestamp': 'DEFAULT CURRENT_TIMESTAMP',
            },
        }

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate CREATE TABLE DDL based on source and target database types.
        
        Input: {
            "source_db": "mysql",
            "target_db": "snowflake",
            "source_table": "table_name",
            "target_table": "target_table_name",
            "columns": [
                {"name": "id", "type": "int", "nullable": False},
                ...
            ],
            "project_id": "optional-for-bigquery",
            "dataset_id": "optional-for-bigquery"
        }
        """
        self.log("Generating DDL with dynamic schema mapping")
        
        source_db = input_data.get("source_db", "mysql").lower()
        target_db = input_data.get("target_db", "snowflake").lower()
        source_table = input_data.get("source_table", "unknown")
        target_table = input_data.get("target_table", "unknown")
        columns = input_data.get("columns", [])
        
        # Optional BigQuery parameters
        project_id = input_data.get("project_id", "")
        dataset_id = input_data.get("dataset_id", "")
        
        if not columns:
            self.log("No columns provided", "error")
            return {"error": "No columns provided"}
        
        # Get DDL template for target database
        template = self.ddl_templates.get(target_db)
        if not template:
            self.log(f"Unsupported target database: {target_db}", "error")
            return {"error": f"Unsupported target database: {target_db}"}
        
        # Generate column definitions
        column_defs = []
        unmapped_types = []
        
        for col in columns:
            col_name = col["name"]
            col_type = col["type"].lower().split('(')[0]  # Remove length/precision
            nullable = col.get("nullable", True)
            
            # Map to target type
            target_type = self._map_type(source_db, col_type, target_db)
            
            if not target_type:
                unmapped_types.append(col_type)
                target_type = "VARCHAR"  # Fallback
                self.log(f"Unmapped type '{col_type}' from {source_db} to {target_db}, using VARCHAR", "warning")
            
            # Handle type parameters (length, precision)
            if '(' in col["type"]:
                params = col["type"][col["type"].find('('):]
                target_type = self._handle_type_params(col_type, params, target_db)
            
            # Format nullable clause based on target database
            null_clause = self._format_nullable(nullable, target_db)
            
            # Format column definition
            col_def = template['column_format'].format(
                column_name=col_name,
                data_type=target_type,
                nullable=null_clause
            )
            column_defs.append(col_def)
        
        # Add metadata columns
        metadata_cols = self._generate_metadata_columns(source_table, target_db, template)
        column_defs.extend(metadata_cols)
        
        # Build CREATE TABLE statement
        table_name = target_table
        if target_db == 'bigquery' and project_id and dataset_id:
            table_name = f"{project_id}.{dataset_id}.{target_table}"
        
        create_ddl = template['table_start'].format(table_name=table_name) + "\n"
        create_ddl += ",\n".join(column_defs) + "\n"
        create_ddl += template['table_end']
        
        # Add comment if supported
        if template['comment_syntax']:
            comment = f"Created by Workflow Studio ETL Pipeline from {source_table} ({source_db})"
            create_ddl += f"\n{template['comment_syntax'].format(comment=comment)}"
        
        self.log(f"Generated DDL for {len(columns)} columns: {source_db} -> {target_db}")
        self.log(f"Target table: {target_table}")
        
        if unmapped_types:
            self.log(f"Unmapped types (used VARCHAR fallback): {set(unmapped_types)}", "warning")
        
        return {
            "ddl": create_ddl.strip(),
            "target_table": target_table,
            "source_table": source_table,
            "source_db": source_db,
            "target_db": target_db,
            "columns_count": len(columns),
            "unmapped_types": list(set(unmapped_types)),
        }
    
    def _map_type(self, source_db: str, source_type: str, target_db: str) -> str:
        """Map source database type to target database type"""
        source_mapping = self.type_mapping_matrix.get(source_db, {})
        type_mapping = source_mapping.get(source_type, {})
        return type_mapping.get(target_db)
    
    def _handle_type_params(self, base_type: str, params: str, target_db: str) -> str:
        """Handle type parameters like VARCHAR(255), DECIMAL(10,2)"""
        if target_db == 'snowflake':
            if base_type in ['varchar', 'char', 'varbinary', 'binary']:
                return f"VARCHAR{params}"
            elif base_type in ['decimal', 'numeric']:
                return f"NUMBER{params}"
        elif target_db == 'bigquery':
            if base_type in ['varchar', 'char', 'nvarchar', 'nchar']:
                return "STRING"  # BigQuery doesn't use length for STRING
            elif base_type in ['decimal', 'numeric']:
                return f"NUMERIC{params}"
        elif target_db == 'redshift':
            if base_type in ['varchar', 'nvarchar']:
                return f"VARCHAR{params}"
            elif base_type in ['decimal', 'numeric']:
                return f"DECIMAL{params}"
        elif target_db == 'postgresql':
            if base_type in ['varchar', 'nvarchar', 'char', 'nchar']:
                return f"VARCHAR{params}"
            elif base_type in ['decimal', 'numeric']:
                return f"NUMERIC{params}"
        
        return base_type  # Return base type if no special handling
    
    def _format_nullable(self, nullable: bool, target_db: str) -> str:
        """Format nullable clause based on target database"""
        if nullable:
            return "NULL" if target_db in ['snowflake', 'redshift'] else ""
        else:
            return "NOT NULL"
    
    def _generate_metadata_columns(self, source_table: str, target_db: str, template: dict) -> list:
        """Generate metadata columns for tracking"""
        metadata_cols = []
        
        # Ingested timestamp
        metadata_cols.append(
            template['column_format'].format(
                column_name="INGESTED_AT",
                data_type="TIMESTAMP" if target_db == 'bigquery' else "TIMESTAMP_NTZ" if target_db == 'snowflake' else "TIMESTAMP",
                nullable="NULL" if target_db in ['snowflake', 'redshift'] else ""
            ) + f" {template['default_timestamp']}"
        )
        
        # Source table name
        metadata_cols.append(
            template['column_format'].format(
                column_name="SOURCE_TABLE",
                data_type="STRING" if target_db == 'bigquery' else "VARCHAR",
                nullable="NULL" if target_db in ['snowflake', 'redshift'] else ""
            ) + f" DEFAULT '{source_table}'"
        )
        
        return metadata_cols