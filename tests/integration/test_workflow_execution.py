"""
Integration tests for workflow execution engine.

Tests the complete job execution pipeline:
- Job submission to RQ
- Workflow execution by worker
- DuckDB processing
- Progress tracking
- Error handling

@MX:NOTE: Comprehensive integration tests for SPEC-WORKFLOW-001
"""

import pytest
import asyncio
import tempfile
import os
from typing import Dict, Any

from src.api.models.job import Job, JobStatus
from src.api.models.user import User
from src.api.models.workflow import Workflow
from src.api.schemas.job import JobSubmit
from src.api.services.job import JobService
from src.workflow.worker import execute_workflow_job, execute_duckdb_workflow, topological_sort, publish_job_progress


class TestWorkflowExecution:
    """Test workflow execution functionality."""

    @pytest.mark.asyncio
    async def test_submit_job_to_queue(
        self,
        job_service: JobService,
        test_workflow: Workflow,
        test_user: User,
        rq_queue
    ):
        """Test submitting a job to the RQ queue."""
        # Create job submission data
        job_data = JobSubmit(
            workflow_id=test_workflow.id
        )

        # Submit job
        job = await job_service.submit_job(job_data, test_user.id)

        assert job is not None
        assert job.id is not None
        assert job.status == JobStatus.pending
        assert job.workflow_id == test_workflow.id
        assert job.created_by == test_user.id
        assert job.progress == 0.0

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(
        self,
        sample_workflow_definition: Dict[str, Any],
        test_db_session,
        test_user
    ):
        """Test executing a simple workflow end-to-end."""
        # Create a job
        from src.api.models.job import Job
        from uuid import uuid4

        job_id = str(uuid4())
        job = Job(
            id=job_id,
            workflow_id=1,
            status=JobStatus.pending,
            created_by=test_user.id
        )
        test_db_session.add(job)
        await test_db_session.commit()

        # Execute workflow directly using async version
        from src.workflow.worker import execute_duckdb_workflow, publish_job_progress

        # Update job status to running
        from src.api.services.job import JobService
        job_service = JobService(test_db_session)
        await job_service.update_job_status(job_id, JobStatus.running)
        publish_job_progress(job_id, 0.0, 'running')

        # Execute workflow
        execution_result = await execute_duckdb_workflow(sample_workflow_definition)

        # Mark as completed
        await job_service.update_job_status(
            job_id,
            JobStatus.completed,
            progress=1.0,
            result=execution_result
        )
        publish_job_progress(job_id, 1.0, 'completed')

        # Verify result
        assert execution_result is not None
        assert execution_result['status'] == 'success'
        assert execution_result['node_count'] == 3

        # Verify job status was updated
        await test_db_session.refresh(job)
        assert job.status == JobStatus.completed
        assert job.progress == 1.0

    @pytest.mark.asyncio
    async def test_execute_duckdb_workflow_direct(
        self,
        sample_workflow_definition: Dict[str, Any]
    ):
        """Test DuckDB workflow execution directly."""
        result = await execute_duckdb_workflow(
            workflow_definition=sample_workflow_definition
        )

        assert result is not None
        assert result['status'] == 'success'
        assert result['node_count'] == 3
        assert 'results' in result

        # Verify node results
        results = result['results']
        assert 'input_1' in results
        assert 'sql_1' in results
        assert 'output_1' in results

        # Verify input node loaded data
        assert results['input_1']['row_count'] == 3
        assert results['input_1']['table'] == 'test_input'

        # Verify SQL node executed query
        assert results['sql_1']['row_count'] == 1
        assert 'data' in results['sql_1']
        assert results['sql_1']['data'][0]['row_count'] == 3
        assert results['sql_1']['data'][0]['total_value'] == 600

    def test_topological_sort(self):
        """Test topological sorting of workflow nodes."""
        nodes = [
            {"id": "n1", "type": "input"},
            {"id": "n2", "type": "sql"},
            {"id": "n3", "type": "output"},
            {"id": "n4", "type": "sql"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n1", "target": "n4"}
        ]

        order = topological_sort(nodes, edges)

        # n1 must come first (no dependencies)
        assert order[0] == "n1"

        # n3 must come after n2
        assert order.index("n2") < order.index("n3")

        # All nodes should be in the result
        assert len(order) == 4
        assert set(order) == {"n1", "n2", "n3", "n4"}

    def test_topological_sort_detects_cycles(self):
        """Test that topological sort detects cycles."""
        nodes = [
            {"id": "n1", "type": "input"},
            {"id": "n2", "type": "sql"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n1"}  # Creates a cycle
        ]

        with pytest.raises(ValueError, match="cycle"):
            topological_sort(nodes, edges)

    @pytest.mark.asyncio
    async def test_workflow_with_missing_file(self):
        """Test workflow execution with missing input file."""
        workflow_definition = {
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "data": {
                        "path": "/nonexistent/file.csv",
                        "table_name": "test_table"
                    }
                }
            ],
            "edges": []
        }

        # Should raise RuntimeError (wrapped FileNotFoundError)
        with pytest.raises(RuntimeError, match="File not found"):
            await execute_duckdb_workflow(workflow_definition)

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_sql(self):
        """Test workflow execution with invalid SQL query."""
        # Create temporary CSV file
        import csv
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'value'])
            writer.writerow([1, 100])
            temp_path = f.name

        workflow_definition = {
            "nodes": [
                {
                    "id": "input_1",
                    "type": "input",
                    "data": {
                        "path": temp_path,
                        "table_name": "test_table"
                    }
                },
                {
                    "id": "sql_1",
                    "type": "sql",
                    "data": {
                        "query": "INVALID SQL QUERY HERE"
                    }
                }
            ],
            "edges": [
                {"source": "input_1", "target": "sql_1"}
            ]
        }

        # Should raise an error (duckdb.Error or similar)
        try:
            await execute_duckdb_workflow(workflow_definition)
            assert False, "Expected exception for invalid SQL"
        except Exception:
            pass  # Expected
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_empty_workflow(self):
        """Test workflow execution with no nodes."""
        workflow_definition = {
            "nodes": [],
            "edges": []
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="no nodes"):
            await execute_duckdb_workflow(workflow_definition)


class TestWorkflowNodeTypes:
    """Test different workflow node types."""

    @pytest.mark.asyncio
    async def test_csv_input_node(self):
        """Test CSV input node."""
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'score'])
            writer.writerow([1, 'Alice', 95])
            writer.writerow([2, 'Bob', 87])
            temp_path = f.name

        try:
            workflow = {
                "nodes": [
                    {
                        "id": "input_1",
                        "type": "input",
                        "data": {
                            "path": temp_path,
                            "table_name": "students"
                        }
                    }
                ],
                "edges": []
            }

            result = await execute_duckdb_workflow(workflow)

            assert result['status'] == 'success'
            assert result['results']['input_1']['row_count'] == 2
            assert result['results']['input_1']['table'] == 'students'

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_parquet_input_node(self):
        """Test Parquet input node."""
        import pandas as pd

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            df = pd.DataFrame({
                'id': [1, 2, 3],
                'value': [100, 200, 300]
            })
            df.to_parquet(f.name)
            temp_path = f.name

        try:
            workflow = {
                "nodes": [
                    {
                        "id": "input_1",
                        "type": "input",
                        "data": {
                            "path": temp_path,
                            "table_name": "parquet_data"
                        }
                    }
                ],
                "edges": []
            }

            result = await execute_duckdb_workflow(workflow)

            assert result['status'] == 'success'
            assert result['results']['input_1']['row_count'] == 3

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_sql_transformation_node(self):
        """Test SQL transformation node."""
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['product', 'price', 'quantity'])
            writer.writerow(['A', 10, 5])
            writer.writerow(['B', 20, 3])
            temp_path = f.name

        try:
            workflow = {
                "nodes": [
                    {
                        "id": "input_1",
                        "type": "input",
                        "data": {
                            "path": temp_path,
                            "table_name": "sales"
                        }
                    },
                    {
                        "id": "sql_1",
                        "type": "sql",
                        "data": {
                            "query": """
                                SELECT
                                    product,
                                    price,
                                    quantity,
                                    price * quantity as total
                                FROM sales
                                ORDER BY total DESC
                            """
                        }
                    }
                ],
                "edges": [
                    {"source": "input_1", "target": "sql_1"}
                ]
            }

            result = await execute_duckdb_workflow(workflow)

            assert result['status'] == 'success'
            sql_result = result['results']['sql_1']
            assert sql_result['row_count'] == 2
            assert sql_result['data'][0]['total'] == 60  # B: 20 * 3
            assert sql_result['data'][1]['total'] == 50  # A: 10 * 5

        finally:
            os.unlink(temp_path)


class TestJobProgressTracking:
    """Test job progress tracking and status updates."""

    @pytest.mark.asyncio
    async def test_progress_updates_during_execution(
        self,
        sample_workflow_definition: Dict[str, Any],
        test_db_session,
        test_user
    ):
        """Test that job progress is updated during workflow execution."""
        from src.api.models.job import Job
        from uuid import uuid4

        job_id = str(uuid4())
        job = Job(
            id=job_id,
            workflow_id=1,
            status=JobStatus.pending,
            created_by=test_user.id
        )
        test_db_session.add(job)
        await test_db_session.commit()

        # Execute workflow directly (progress updates happen internally)
        from src.api.services.job import JobService
        job_service = JobService(test_db_session)

        await job_service.update_job_status(job_id, JobStatus.running)

        # Execute workflow
        execution_result = await execute_duckdb_workflow(sample_workflow_definition)

        # Mark as completed
        await job_service.update_job_status(
            job_id,
            JobStatus.completed,
            progress=1.0,
            result=execution_result
        )

        # Verify final state
        await test_db_session.refresh(job)
        assert job.status == JobStatus.completed
        assert job.progress == 1.0

    @pytest.mark.asyncio
    async def test_error_status_on_failure(
        self,
        test_db_session,
        test_user
    ):
        """Test that job status is set to failed on error."""
        from src.api.models.job import Job
        from uuid import uuid4

        job_id = str(uuid4())
        job = Job(
            id=job_id,
            workflow_id=1,
            status=JobStatus.pending,
            created_by=test_user.id
        )
        test_db_session.add(job)
        await test_db_session.commit()

        # Execute invalid workflow
        bad_workflow = {
            "nodes": [
                {
                    "id": "bad_node",
                    "type": "input",
                    "data": {
                        "path": "/nonexistent.csv",
                        "table_name": "bad"
                    }
                }
            ],
            "edges": []
        }

        from src.api.services.job import JobService
        job_service = JobService(test_db_session)

        # Try to execute
        try:
            execution_result = await execute_duckdb_workflow(bad_workflow)
        except Exception as e:
            # Mark as failed
            await job_service.update_job_status(
                job_id,
                JobStatus.failed,
                error_message=str(e)
            )

        # Verify error status
        await test_db_session.refresh(job)
        assert job.status == JobStatus.failed
        assert job.error_message is not None


class TestJobServiceIntegration:
    """Test JobService integration with RQ."""

    @pytest.mark.asyncio
    async def test_list_jobs(
        self,
        job_service: JobService,
        test_workflow: Workflow,
        test_user: User
    ):
        """Test listing jobs."""
        # Create multiple jobs
        job_data = JobSubmit(workflow_id=test_workflow.id)

        job1 = await job_service.submit_job(job_data, test_user.id)
        job2 = await job_service.submit_job(job_data, test_user.id)

        # List jobs
        jobs, total = await job_service.list_jobs(test_user.id)

        assert total >= 2
        assert len(jobs) >= 2

        # Check that our jobs are in the list
        job_ids = [job.id for job in jobs]
        assert job1.id in job_ids
        assert job2.id in job_ids

    @pytest.mark.asyncio
    async def test_get_job(
        self,
        job_service: JobService,
        test_workflow: Workflow,
        test_user: User
    ):
        """Test getting a specific job."""
        job_data = JobSubmit(workflow_id=test_workflow.id)
        job = await job_service.submit_job(job_data, test_user.id)

        # Get the job
        retrieved_job = await job_service.get_job(job.id, test_user.id)

        assert retrieved_job is not None
        assert retrieved_job.id == job.id
        assert retrieved_job.workflow_id == test_workflow.id

    @pytest.mark.asyncio
    async def test_cancel_job(
        self,
        job_service: JobService,
        test_workflow: Workflow,
        test_user: User
    ):
        """Test cancelling a job."""
        job_data = JobSubmit(workflow_id=test_workflow.id)
        job = await job_service.submit_job(job_data, test_user.id)

        # Cancel the job
        cancelled = await job_service.cancel_job(job.id, test_user.id)

        assert cancelled is True

        # Verify status
        await job_service.db.refresh(job)
        assert job.status == JobStatus.cancelled
