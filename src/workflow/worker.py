"""
RQ Worker for SPEC-WORKFLOW-001 Workflow Automation System

Background worker for handling workflow task processing including:
- SPEC execution tasks
- Document generation tasks
- Database migration tasks
- System monitoring tasks

@MX:NOTE: Worker executes RQ jobs synchronously, bridges to async JobService via run_sync
"""

import os
import sys
import json
import logging
import asyncio
import duckdb
import redis
from typing import Dict, Any, Optional, Callable, List
from rq import Worker, Queue
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global Redis connection (reused across jobs)
redis_conn: Optional[redis.Redis] = None


def get_redis_connection() -> redis.Redis:
    """Get Redis connection with configuration from environment

    @MX:ANCHOR: Redis connection factory (fan_in: worker main, execute_workflow_job, pubsub)
    @MX:REASON: Centralized connection management ensures proper pooling and error handling
    """
    global redis_conn

    if redis_conn is None:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))

        try:
            redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False  # Keep binary for pub/sub
            )
            # Test connection
            redis_conn.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    return redis_conn


def run_sync(coroutine):
    """Run an async coroutine in a sync context

    @MX:NOTE: Bridge between RQ sync workers and async SQLAlchemy service layer
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context (pytest-asyncio), create new loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop exists, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coroutine)


async def execute_workflow_job_async(job_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async wrapper for workflow execution (for testing purposes).

    Args:
        job_id: Job identifier (UUID string)
        workflow_definition: Workflow graph with nodes, edges, and configuration

    Returns:
        Dict containing execution results

    @MX:NOTE: Async version for pytest-asyncio testing
    """
    from src.api.models.job import JobStatus

    session = None
    job_service = None
    result = {'status': 'failed', 'error': 'Unknown error'}

    try:
        logger.info(f"Starting async workflow execution for job {job_id}")

        # Import JobService here to avoid circular imports
        from src.api.services.job import JobService
        from src.api.models.base import get_async_session

        # Create async session and service properly using async context manager
        async with get_async_session() as session:
            job_service = JobService(session)

            # Update job status to running
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.running
            )
            publish_job_progress(job_id, 0.0, 'running', message='Starting workflow execution')

            # Execute workflow using DuckDB
            execution_result = await execute_duckdb_workflow(
                workflow_definition=workflow_definition,
                progress_callback=lambda p: publish_job_progress(
                    job_id, p, 'running',
                    message=f'Processing workflow: {p:.1%} complete'
                )
            )

            # Mark as completed
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.completed,
                progress=1.0,
                result=execution_result
            )
            publish_job_progress(job_id, 1.0, 'completed', message='Workflow execution completed successfully')

            result = {
                'status': 'success',
                'job_id': job_id,
                'result': execution_result
            }

            logger.info(f"Async workflow execution completed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Async workflow execution failed for job {job_id}: {error_msg}", exc_info=True)

        result = {
            'status': 'failed',
            'job_id': job_id,
            'error': error_msg
        }

        # Update job status to failed
        try:
            if job_service and job_id:
                await job_service.update_job_status(
                    job_id=job_id,
                    status=JobStatus.failed,
                    error_message=error_msg
                )
                publish_job_progress(job_id, -1.0, 'failed', message=error_msg)
        except Exception as update_error:
            logger.error(f"Failed to update job status after error: {update_error}")

    return result


def publish_job_progress(job_id: str, progress: float, status: str, **extra_data):
    """Publish job progress update to Redis pub/sub

    Args:
        job_id: Job UUID
        progress: Progress value (0.0 to 1.0)
        status: Current status string
        **extra_data: Additional fields to include in message
    """
    try:
        message = {
            'job_id': job_id,
            'progress': progress,
            'status': status,
            'timestamp': asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0,
            **extra_data
        }

        conn = get_redis_connection()
        conn.publish(
            f"job_progress:{job_id}",
            json.dumps(message)
        )
        logger.debug(f"Published progress for job {job_id}: {progress:.1%}")
    except Exception as e:
        logger.warning(f"Failed to publish progress: {e}")


async def execute_comprehensive_workflow(job_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute comprehensive workflow using existing workflow execution logic.

    This function bridges the RQ job system with the comprehensive workflow
    execution engine in src/api/routes/workflows.py.

    Args:
        job_id: Job identifier (UUID string)
        workflow_definition: Workflow graph with nodes, edges, and configuration

    Returns:
        Dict containing execution results

    @MX:NOTE: Bridges RQ background jobs with existing comprehensive workflow execution
    """
    from src.api.models.job import JobStatus
    from src.api.routes.workflows import execute_workflow_graph
    from src.api.schemas.workflow import WorkflowExecutionRequest

    job_service = None
    result = {'status': 'failed', 'error': 'Unknown error'}

    try:
        logger.info(f"Starting comprehensive workflow execution for job {job_id}")

        # Import JobService here to avoid circular imports
        from src.api.services.job import JobService
        from src.api.models import get_async_session

        # Create async session and service properly using async context manager
        async with get_async_session() as session:
            job_service = JobService(session)

            # Update job status to running
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.running
            )
            publish_job_progress(job_id, 0.0, 'running', message='Starting comprehensive workflow execution')

            # Import the comprehensive execution logic
            # We need to call it but we can't easily since it's in a request handler
            # So we'll replicate the key parts here

            # For now, use the simpler duckdb workflow execution
            # TODO: Integrate full comprehensive execution (all 20+ node types)

            execution_result = await execute_duckdb_workflow(
                workflow_definition=workflow_definition,
                progress_callback=lambda p: publish_job_progress(
                    job_id, p, 'running',
                    message=f'Processing workflow: {p:.1%} complete'
                )
            )

            # Mark as completed
            await job_service.update_job_status(
                job_id=job_id,
                status=JobStatus.completed,
                progress=1.0,
                result=execution_result
            )
            publish_job_progress(job_id, 1.0, 'completed', message='Workflow execution completed successfully')

            result = {
                'status': 'success',
                'job_id': job_id,
                'result': execution_result
            }

            logger.info(f"Comprehensive workflow execution completed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Comprehensive workflow execution failed for job {job_id}: {error_msg}", exc_info=True)

        result = {
            'status': 'failed',
            'job_id': job_id,
            'error': error_msg
        }

        # Update job status to failed
        try:
            if job_id:
                # Create a new session for the error update
                async def update_error_status():
                    from src.api.services.job import JobService
                    from src.api.models import get_async_session

                    async with get_async_session() as session:
                        job_service = JobService(session)
                        await job_service.update_job_status(
                            job_id=job_id,
                            status=JobStatus.failed,
                            error_message=error_msg
                        )

                await update_error_status()
                publish_job_progress(job_id, -1.0, 'failed', message=error_msg)
        except Exception as update_error:
            logger.error(f"Failed to update job status after error: {update_error}")

    return result


def execute_workflow_job(job_id: str, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow job. This function is called by RQ workers.

    Args:
        job_id: Job identifier (UUID string)
        workflow_definition: Workflow graph with nodes, edges, and configuration

    Returns:
        Dict containing execution results

    @MX:ANCHOR: RQ job entry point for workflow execution (fan_in: JobService.submit_job, test suite, direct enqueue)
    @MX:REASON: Single entry point ensures consistent job execution tracking and error handling
    """
    from src.api.models.job import JobStatus

    result = {'status': 'failed', 'error': 'Unknown error'}

    try:
        logger.info(f"Starting workflow execution for job {job_id}")

        # Import JobService here to avoid circular imports
        from src.api.services.job import JobService
        from src.api.models import get_async_session

        # Create async session and service properly using async context manager
        async def execute_workflow():
            async with get_async_session() as session:
                job_service = JobService(session)

                # Update job status to running
                await job_service.update_job_status(
                    job_id=job_id,
                    status=JobStatus.running
                )
                publish_job_progress(job_id, 0.0, 'running', message='Starting workflow execution')

                # Execute workflow using DuckDB
                execution_result = await execute_duckdb_workflow(
                    workflow_definition=workflow_definition,
                    progress_callback=lambda p: publish_job_progress(
                        job_id, p, 'running',
                        message=f'Processing workflow: {p:.1%} complete'
                    )
                )

                # Mark as completed
                await job_service.update_job_status(
                    job_id=job_id,
                    status=JobStatus.completed,
                    progress=1.0,
                    result=execution_result
                )
                publish_job_progress(job_id, 1.0, 'completed', message='Workflow execution completed successfully')

                return {
                    'status': 'success',
                    'job_id': job_id,
                    'result': execution_result
                }

        result = run_sync(execute_workflow())
        logger.info(f"Workflow execution completed successfully for job {job_id}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Workflow execution failed for job {job_id}: {error_msg}", exc_info=True)

        result = {
            'status': 'failed',
            'job_id': job_id,
            'error': error_msg
        }

        # Update job status to failed
        try:
            if job_id:
                # Create a new session for the error update
                async def update_error_status():
                    from src.api.services.job import JobService
                    from src.api.models import get_async_session

                    async with get_async_session() as session:
                        job_service = JobService(session)
                        await job_service.update_job_status(
                            job_id=job_id,
                            status=JobStatus.failed,
                            error_message=error_msg
                        )

                run_sync(update_error_status())
                publish_job_progress(job_id, -1.0, 'failed', message=error_msg)
        except Exception as update_error:
            logger.error(f"Failed to update job status after error: {update_error}")

    return result


async def execute_duckdb_workflow(
    workflow_definition: Dict[str, Any],
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    Execute a DuckDB workflow graph.

    This is the core execution engine that:
    1. Parses the workflow graph (nodes + edges)
    2. Executes nodes in topological order
    3. Passes data between nodes via DuckDB
    4. Tracks progress

    Args:
        workflow_definition: Workflow dict with 'nodes' and 'edges' keys
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with execution results and statistics

    @MX:ANCHOR: Core workflow execution logic using in-memory DuckDB (fan_in: execute_workflow_job_async, execute_workflow_job, test suite)
    @MX:REASON: Single execution engine ensures consistent node ordering and error handling
    """
    import duckdb

    # Validate workflow definition
    if not workflow_definition or "nodes" not in workflow_definition:
        raise ValueError("Invalid workflow definition: missing 'nodes' field")

    nodes = workflow_definition.get('nodes', [])
    edges = workflow_definition.get('edges', [])

    if not nodes:
        raise ValueError("Workflow has no nodes to execute")

    # Create in-memory DuckDB connection
    con = duckdb.connect(":memory:")

    # Build execution order (topological sort)
    execution_order = topological_sort(nodes, edges)

    results = {}
    total_nodes = len(execution_order)

    logger.info(f"Executing {total_nodes} nodes in topological order")

    for i, node_id in enumerate(execution_order):
        node = next((n for n in nodes if n['id'] == node_id), None)
        if not node:
            raise ValueError(f"Node {node_id} not found in workflow definition")

        logger.info(f"Executing node {node_id} (type: {node.get('type')})")

        # Execute node based on type
        try:
            node_result = await execute_node(con, node, results)
            results[node_id] = node_result

            # Update progress
            if progress_callback:
                progress = (i + 1) / total_nodes
                progress_callback(progress)

        except Exception as e:
            raise RuntimeError(f"Node {node_id} execution failed: {str(e)}") from e

    return {
        'status': 'success',
        'results': results,
        'node_count': total_nodes
    }


async def execute_node(con: duckdb.DuckDBPyConnection, node: Dict, context: Dict) -> Any:
    """
    Execute a single workflow node.

    Args:
        con: DuckDB connection
        node: Node definition dict
        context: Results from previously executed nodes

    Returns:
        Node execution result

    @MX:ANCHOR: Node execution dispatcher - routes to specific node type handlers (fan_in: execute_duckdb_workflow)
    @MX:REASON: Single entry point for all node types ensures consistent error handling and result tracking
    """
    node_type = node.get('type')
    data = node.get('data', {})
    node_id = node.get('id', 'unknown')

    logger.debug(f"Executing node {node_id} of type {node_type}")

    if node_type == 'input':
        # Handle CSV/file input
        return await execute_input_node(con, data)

    elif node_type == 'sql':
        # Execute SQL query
        return await execute_sql_node(con, data, context)

    elif node_type == 'output':
        # Export result
        return await execute_output_node(con, data, context)

    else:
        raise ValueError(f"Unknown node type: {node_type}")


async def execute_input_node(con: duckdb.DuckDBPyConnection, data: Dict) -> Dict[str, Any]:
    """Execute an input node (CSV/Parquet file load)"""
    import os

    file_path = data.get('path', '')
    table_name = data.get('table_name', 'input_table')

    if not file_path:
        raise ValueError("Input node missing 'path' parameter")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect file type and load
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.csv':
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
    elif file_ext == '.parquet':
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')")
    elif file_ext == '.json':
        con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto('{file_path}')")
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

    # Get row count
    row_count_result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    row_count = row_count_result[0] if row_count_result else 0

    return {
        'table': table_name,
        'row_count': row_count,
        'file_path': file_path
    }


async def execute_sql_node(con: duckdb.DuckDBPyConnection, data: Dict, context: Dict) -> Dict[str, Any]:
    """Execute a SQL transformation node"""
    query = data.get('query', '')

    if not query:
        raise ValueError("SQL node missing 'query' parameter")

    # Execute query
    result_df = con.execute(query).fetchdf()

    return {
        'data': result_df.to_dict('records'),
        'row_count': len(result_df),
        'columns': list(result_df.columns)
    }


async def execute_output_node(con: duckdb.DuckDBPyConnection, data: Dict, context: Dict) -> Dict[str, Any]:
    """Execute an output node (export result)"""
    source_node = data.get('source', '')

    if not source_node or source_node not in context:
        raise ValueError(f"Output node references invalid source: {source_node}")

    return context[source_node]


def topological_sort(nodes: List[Dict], edges: List[Dict]) -> List[str]:
    """
    Sort nodes in execution order using topological sort (Kahn's algorithm).

    Args:
        nodes: List of node definitions
        edges: List of edge definitions

    Returns:
        List of node IDs in execution order

    @MX:NOTE: Implements Kahn's algorithm for topological sorting
    @MX:WARN: Does not detect cycles - assumes valid DAG from UI
    @MX:REASON: UI validation ensures DAG; cycle detection would be defensive programming
    """
    # Build adjacency list and in-degree count
    node_ids = [n['id'] for n in nodes]
    graph = {node_id: [] for node_id in node_ids}
    in_degree = {node_id: 0 for node_id in node_ids}

    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')

        if source and target and source in in_degree and target in in_degree:
            graph[source].append(target)
            in_degree[target] += 1

    # Initialize queue with nodes having no dependencies
    queue = [node_id for node_id in node_ids if in_degree[node_id] == 0]
    result = []

    while queue:
        node_id = queue.pop(0)
        result.append(node_id)

        for neighbor in graph[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(node_ids):
        raise ValueError("Workflow contains a cycle - cannot execute")

    return result


def main():
    """Start the RQ worker"""
    try:
        conn = get_redis_connection()

        # Configure queues
        queues = [
            Queue('spec_execution', connection=conn),
            Queue('document_generation', connection=conn),
            Queue('database_migrations', connection=conn),
            Queue('system_monitoring', connection=conn),
            Queue('default', connection=conn),
        ]

        # Create worker
        worker = Worker(queues, connection=conn)

        # Configure worker behavior
        logger.info(f"Starting RQ worker with queues: {[q.name for q in queues]}")

        # Start worker
        worker.work()

    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        raise


if __name__ == '__main__':
    main()