from fastapi import APIRouter, HTTPException

from app.schemas.studio import SaveConnectionRequest, SavePipelineRequest
from app.services.pipeline_service import PipelineService
from app.etl_runtime import SnowflakeConnector, MySQLConnector

router = APIRouter()
service = PipelineService()


@router.get("/executors")
def get_executors() -> list[dict[str, str]]:
    return service.executor_catalog()


@router.get("/connections")
def get_connections():
    return service.list_connections()


@router.post("/connections")
def create_connection(payload: SaveConnectionRequest):
    return service.save_connection(payload)


@router.put("/connections/{connection_id}")
def update_connection(connection_id: str, payload: SaveConnectionRequest):
    return service.save_connection(payload, connection_id=connection_id)


@router.delete("/connections/{connection_id}")
def remove_connection(connection_id: str):
    service.delete_connection(connection_id)
    return {"ok": True}

@router.post("/connections/{connection_id}/test")
async def test_connection(connection_id: str):
    """Test if a connection is working"""
    connections = service.list_connections()
    conn = next((c for c in connections if c.id == connection_id), None)
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    config = service._to_connection_config(conn)
    
    try:
        if conn.type == "snowflake":
            from app.etl_runtime import SnowflakeConnector
            connector = SnowflakeConnector(config)
            
            await connector.connect()
            
            if connector._simulate:
                return {
                    "status": "simulation",
                    "message": "Running in simulation mode - missing required fields",
                    "details": {
                        "account": config.account,
                        "user": config.user,
                        "database": config.database,
                        "warehouse": config.warehouse
                    }
                }
            
            # Test query
            result = await connector.execute_query("SELECT CURRENT_TIMESTAMP() as now")
            await connector.disconnect()
            
            return {
                "status": "success",
                "message": "Connection successful!",
                "result": result
            }
            
        elif conn.type == "mysql":
            from app.etl_runtime import MySQLConnector
            connector = MySQLConnector(config)
            
            await connector.connect()
            
            if connector._simulate:
                return {
                    "status": "simulation",
                    "message": "Running in simulation mode - missing required fields",
                    "details": {
                        "host": config.host,
                        "user": config.user,
                        "database": config.database
                    }
                }
            
            # Test query
            result = await connector.execute_query("SELECT NOW() as now")
            await connector.disconnect()
            
            return {
                "status": "success",
                "message": "Connection successful!",
                "result": result
            }
        else:
            return {
                "status": "unsupported",
                "message": f"Testing not implemented for {conn.type} connections"
            }
            
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Connection failed: {str(e)}",
            "error": str(e)
        }

@router.get("/pipelines")
def get_pipelines():
    return service.list_pipelines()


@router.post("/pipelines")
def create_pipeline(payload: SavePipelineRequest):
    return service.save_pipeline(payload)


@router.put("/pipelines/{pipeline_id}")
def update_pipeline(pipeline_id: str, payload: SavePipelineRequest):
    return service.save_pipeline(payload, pipeline_id=pipeline_id)


@router.delete("/pipelines/{pipeline_id}")
def remove_pipeline(pipeline_id: str):
    service.delete_pipeline(pipeline_id)
    return {"ok": True}


@router.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: str):
    try:
        execution = service.run_pipeline(pipeline_id)
        return {"execution": execution}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/executions")
def get_executions():
    return service.list_executions()


@router.delete("/executions/{execution_id}")
def delete_execution(execution_id: str):
    service.delete_execution(execution_id)
    return {"ok": True}


@router.delete("/executions")
def clear_all_executions():
    service.clear_all_executions()
    return {"ok": True}