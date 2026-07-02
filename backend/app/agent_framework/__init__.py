# backend/app/agent_framework/__init__.py

from typing import Any, Iterator, List
from abc import ABC, abstractmethod

# 1. Define WorkflowRunResult first so it's always available
class WorkflowRunResult:
    def __init__(self, events: List[Any] = None):
        self._events = events or []

    def __iter__(self) -> Iterator[Any]:
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

# 2. Define Executor base class
class Executor(ABC):
    executor_type: str = "base_executor"

    def __init__(self, id: str):
        self.id = id

    def execute(self, context, node_data):
        return {} 

# 3. Define handler decorator
def handler(func):
    """Decorator to mark a method as a workflow execution step."""
    func._is_handler = True
    return func

# 4. Define WorkflowContext
class WorkflowContext:
    def __init__(self, pipeline_id: str = None):
        self.pipeline_id = pipeline_id
        self.state = {}
        
    def set_state(self, key, value):
        self.state[key] = value
        
    def get_state(self, key, default=None):
        return self.state.get(key, default)

    async def yield_output(self, data):
        pass
        
    async def send_message(self, data):
        pass

# 5. Define WorkflowBuilder
class WorkflowBuilder:
    def __init__(self, name="", description="", start_executor=None, output_from=None, intermediate_output_from=None):
        self.name = name
        self.description = description
        self.start_executor = start_executor
        self.edges = []
        
    def add_edge(self, source, target, condition=None):
        self.edges.append({
            "source": source, 
            "target": target, 
            "condition": condition
        })
        
    def build(self):
        return SimpleWorkflow(self.start_executor, self.edges)

class SimpleWorkflow:
    def __init__(self, start_executor, edges):
        self.start_executor = start_executor
        self.edges = edges
        self.executed = {}

    async def _execute_executor(self, executor, input_data, pipeline_id=None):
        """Execute a single executor and return its output"""
        import inspect
        
        # Create context for this executor - PASS pipeline_id
        ctx = WorkflowContext(pipeline_id=pipeline_id)
        ctx.state = {}
        
        # Check if executor has async process method
        if hasattr(executor, 'process'):
            if inspect.iscoroutinefunction(executor.process):
                result = await executor.process(input_data, ctx)
            else:
                result = executor.process(input_data, ctx)
            return result, ctx
        else:
            return executor.execute(ctx, {}), ctx

    async def run(self, context):
        """Execute the workflow by following edges"""
        import logging
        logger = logging.getLogger(__name__)
        
        events = []
        
        # Extract pipeline_id from context if available
        pipeline_id = None
        if isinstance(context, dict):
            pipeline_id = context.get("pipeline_id")
        
        # Start with the first executor
        if not self.start_executor:
            logger.error("No start executor defined")
            return WorkflowRunResult(events)
        
        # Execute start executor with empty input
        logger.info(f"Starting workflow with executor: {self.start_executor.id}")
        current_output, current_ctx = await self._execute_executor(self.start_executor, {}, pipeline_id)
        self.executed[self.start_executor.id] = current_output
        events.append({"type": "output", "executor_id": self.start_executor.id, "data": current_output})
        
        # ... (rest of the run method stays the same, but update all _execute_executor calls to pass pipeline_id)
        
        # Build a map of executor ID -> executor object
        executor_map = {}
        for edge in self.edges:
            if hasattr(edge['source'], 'id'):
                executor_map[edge['source'].id] = edge['source']
            if hasattr(edge['target'], 'id'):
                executor_map[edge['target'].id] = edge['target']
        
        # Add start executor to map
        if hasattr(self.start_executor, 'id'):
            executor_map[self.start_executor.id] = self.start_executor
        
        # Track which executors need to run
        to_execute = [(self.start_executor, current_output)]
        executed_ids = {self.start_executor.id}
        
        # Follow edges and execute connected executors
        max_iterations = len(self.edges) * 2
        iteration = 0
        
        while to_execute and iteration < max_iterations:
            iteration += 1
            source_executor, source_output = to_execute.pop(0)
            
            for edge in self.edges:
                edge_source = edge['source'] if hasattr(edge['source'], 'id') else edge['source']
                edge_target = edge['target'] if hasattr(edge['target'], 'id') else edge['target']
                
                source_id = source_executor.id if hasattr(source_executor, 'id') else source_executor
                target_id = edge_target.id if hasattr(edge_target, 'id') else edge_target
                
                if edge_source == source_executor or (hasattr(edge_source, 'id') and edge_source.id == source_id):
                    condition = edge.get('condition')
                    if condition:
                        if not condition(source_output):
                            logger.info(f"Skipping edge to {target_id} - condition not met")
                            continue
                    
                    if target_id not in executed_ids and target_id in executor_map:
                        target_executor = executor_map[target_id]
                        logger.info(f"Executing {target_id} with input keys: {list(source_output.keys()) if isinstance(source_output, dict) else 'N/A'}")
                        
                        try:
                            # PASS pipeline_id HERE
                            output, ctx = await self._execute_executor(target_executor, source_output, pipeline_id)
                            self.executed[target_id] = output
                            events.append({"type": "output", "executor_id": target_id, "data": output})
                            executed_ids.add(target_id)
                            
                            to_execute.append((target_executor, output))
                            logger.info(f"✅ {target_id} completed. Output keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}")
                            
                        except Exception as e:
                            logger.error(f"Error executing {target_id}: {e}", exc_info=True)
                            events.append({"type": "error", "executor_id": target_id, "error": str(e)})
        
        logger.info(f"Workflow completed. Executed {len(executed_ids)} executors")
        return WorkflowRunResult(events)