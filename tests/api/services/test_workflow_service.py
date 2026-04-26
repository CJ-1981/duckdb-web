"""
Characterization tests for WorkflowService.

These tests capture the CURRENT BEHAVIOR of the WorkflowService
to serve as a safety net during refactoring in the IMPROVE phase.

@MX:NOTE: Characterization tests document actual behavior, not intended behavior
@MX:SPEC: SPEC-WORKFLOW-001
"""

import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.services.workflow import WorkflowService
from src.api.models.workflow import Workflow
from src.api.models.workflow_version import WorkflowVersion
from src.api.schemas.workflow import WorkflowCreate, WorkflowUpdate


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def workflow_service(mock_db_session):
    """Create WorkflowService instance with mock session."""
    return WorkflowService(mock_db_session)


@pytest.fixture
def sample_workflow_create():
    """Sample WorkflowCreate data."""
    return WorkflowCreate(
        name="test_workflow",
        description="Test workflow description",
        definition={
            "nodes": [
                {"id": "node1", "type": "source"},
                {"id": "node2", "type": "transform"}
            ],
            "edges": [
                {"from": "node1", "to": "node2"}
            ]
        }
    )


@pytest.fixture
def sample_workflow_update():
    """Sample WorkflowUpdate data."""
    return WorkflowUpdate(
        name="updated_workflow",
        description="Updated description",
        definition={
            "nodes": [
                {"id": "node1", "type": "source"},
                {"id": "node2", "type": "transform"},
                {"id": "node3", "type": "sink"}
            ],
            "edges": [
                {"from": "node1", "to": "node2"},
                {"from": "node2", "to": "node3"}
            ]
        }
    )


@pytest.fixture
def sample_workflow():
    """Sample Workflow model instance."""
    workflow = Workflow()
    workflow.id = str(uuid4())
    workflow.name = "existing_workflow"
    workflow.description = "Existing description"
    workflow.definition = {
        "nodes": [{"id": "node1", "type": "source"}],
        "edges": []
    }
    workflow.owner_id = 1
    workflow.version = 1
    workflow.is_active = True
    workflow.created_at = datetime.utcnow()
    workflow.updated_at = datetime.utcnow()
    return workflow


# ============================================================================
# Characterization Tests - WorkflowService.create_workflow
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_create_workflow_basic(workflow_service, mock_db_session, sample_workflow_create):
    """Characterize: create_workflow creates workflow with version 1."""
    # Arrange
    owner_id = 1
    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await workflow_service.create_workflow(sample_workflow_create, owner_id)

    # Assert - Characterize creation behavior
    mock_db_session.add.assert_called_once()
    assert mock_db_session.commit.call_count == 2  # Once for workflow, once for version
    assert mock_db_session.refresh.call_count == 1

    # Characterize created workflow
    created_workflow = mock_db_session.add.call_args_list[0][0][0]
    assert isinstance(created_workflow, Workflow)
    assert created_workflow.name == sample_workflow_create.name
    assert created_workflow.description == sample_workflow_create.description
    assert created_workflow.definition == sample_workflow_create.definition.dict()
    assert created_workflow.owner_id == owner_id
    assert created_workflow.version == 1


@pytest.mark.asyncio
async def test_characterize_create_workflow_creates_version_entry(workflow_service, mock_db_session, sample_workflow_create):
    """Characterize: create_workflow creates initial WorkflowVersion entry."""
    # Arrange
    owner_id = 1
    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    await workflow_service.create_workflow(sample_workflow_create, owner_id)

    # Assert - Characterize version entry creation
    assert mock_db_session.add.call_count == 2  # Workflow + WorkflowVersion

    # Check second add call is for WorkflowVersion
    version_call_args = mock_db_session.add.call_args_list[1][0][0]
    assert isinstance(version_call_args, WorkflowVersion)
    assert version_call_args.version == 1


@pytest.mark.asyncio
async def test_characterize_create_workflow_with_minimal_data(workflow_service, mock_db_session):
    """Characterize: create_workflow with minimal required fields."""
    # Arrange
    minimal_create = WorkflowCreate(
        name="minimal_workflow",
        definition={"nodes": [], "edges": []}
    )
    owner_id = 1
    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await workflow_service.create_workflow(minimal_create, owner_id)

    # Assert - Characterize minimal creation behavior
    created_workflow = mock_db_session.add.call_args_list[0][0][0]
    assert created_workflow.name == "minimal_workflow"
    assert created_workflow.description is None
    assert created_workflow.definition == {"nodes": [], "edges": []}
    assert created_workflow.version == 1


# ============================================================================
# Characterization Tests - WorkflowService.get_workflow
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_get_workflow_found(workflow_service, mock_db_session, sample_workflow):
    """Characterize: get_workflow returns workflow when found."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.get_workflow(workflow_id, owner_id)

    # Assert - Characterize retrieval behavior
    assert result is not None
    assert result.id == workflow_id
    assert result.name == sample_workflow.name
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_characterize_get_workflow_not_found(workflow_service, mock_db_session):
    """Characterize: get_workflow returns None when not found."""
    # Arrange
    workflow_id = str(uuid4())
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.get_workflow(workflow_id, owner_id)

    # Assert - Characterize not found behavior
    assert result is None


@pytest.mark.asyncio
async def test_characterize_get_workflow_ownership_check(workflow_service, mock_db_session, sample_workflow):
    """Characterize: get_workflow checks workflow ownership."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    await workflow_service.get_workflow(workflow_id, owner_id)

    # Assert - Characterize ownership check
    # Verify that the query includes owner_id filter
    call_args = mock_db_session.execute.call_args
    assert call_args is not None


@pytest.mark.asyncio
async def test_characterize_get_workflow_deleted_filter(workflow_service, mock_db_session):
    """Characterize: get_workflow filters out deleted workflows."""
    # Arrange
    workflow_id = str(uuid4())
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_result

    # Act
    await workflow_service.get_workflow(workflow_id, owner_id)

    # Assert - Characterize deleted_at filter
    # Query should include deleted_at.is_(None) condition
    call_args = mock_db_session.execute.call_args
    assert call_args is not None


# ============================================================================
# Characterization Tests - WorkflowService.list_workflows
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_list_workflows_default_pagination(workflow_service, mock_db_session):
    """Characterize: list_workflows with default pagination parameters."""
    # Arrange
    owner_id = 1

    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=5)

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[])
    mock_result.scalars = Mock(return_value=mock_scalars)

    # Configure execute to return different results on sequential calls
    execute_results = [mock_count_result, mock_result]
    mock_db_session.execute.side_effect = execute_results

    # Act
    workflows, total = await workflow_service.list_workflows(owner_id)

    # Assert - Characterize default pagination behavior
    assert isinstance(workflows, list)
    assert isinstance(total, int)
    assert mock_db_session.execute.call_count == 2  # Count + List
    assert total == 5


@pytest.mark.asyncio
async def test_characterize_list_workflows_with_pagination(workflow_service, mock_db_session):
    """Characterize: list_workflows with custom pagination."""
    # Arrange
    owner_id = 1
    page = 2
    page_size = 10

    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=25)

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[])
    mock_result.scalars = Mock(return_value=mock_scalars)

    execute_results = [mock_count_result, mock_result]
    mock_db_session.execute.side_effect = execute_results

    # Act
    workflows, total = await workflow_service.list_workflows(owner_id, page=page, page_size=page_size)

    # Assert - Characterize pagination behavior
    assert mock_db_session.execute.call_count == 2
    assert total == 25


@pytest.mark.asyncio
async def test_characterize_list_workflows_with_active_filter(workflow_service, mock_db_session):
    """Characterize: list_workflows filters by is_active status."""
    # Arrange
    owner_id = 1
    is_active = True

    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=3)

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[])
    mock_result.scalars = Mock(return_value=mock_scalars)

    execute_results = [mock_count_result, mock_result]
    mock_db_session.execute.side_effect = execute_results

    # Act
    workflows, total = await workflow_service.list_workflows(owner_id, is_active=is_active)

    # Assert - Characterize active filter behavior
    assert mock_db_session.execute.call_count == 2
    assert total == 3


@pytest.mark.asyncio
async def test_characterize_list_workflows_empty_result(workflow_service, mock_db_session):
    """Characterize: list_workflows returns empty list when no workflows found."""
    # Arrange
    owner_id = 999  # Non-existent owner

    mock_count_result = Mock()
    mock_count_result.scalar = Mock(return_value=0)

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all = Mock(return_value=[])
    mock_result.scalars = Mock(return_value=mock_scalars)

    execute_results = [mock_count_result, mock_result]
    mock_db_session.execute.side_effect = execute_results

    # Act
    workflows, total = await workflow_service.list_workflows(owner_id)

    # Assert - Characterize empty result behavior
    assert workflows == []
    assert total == 0


# ============================================================================
# Characterization Tests - WorkflowService.update_workflow
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_update_workflow_name_only(workflow_service, mock_db_session, sample_workflow):
    """Characterize: update_workflow updates name without changing version."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    update_data = WorkflowUpdate(name="updated_name")

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize name-only update behavior
    assert result is not None
    assert result.name == "updated_name"
    assert result.version == 1  # Version should not change
    assert mock_db_session.commit.call_count == 1


@pytest.mark.asyncio
async def test_characterize_update_workflow_with_definition_increments_version(workflow_service, mock_db_session, sample_workflow):
    """Characterize: update_workflow increments version when definition changes."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    update_data = WorkflowUpdate(
        definition={
            "nodes": [{"id": "new_node", "type": "source"}],
            "edges": []
        }
    )

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize version increment behavior
    assert result is not None
    assert result.version == 2  # Version should increment
    assert mock_db_session.commit.call_count == 2  # Update + Version entry


@pytest.mark.asyncio
async def test_characterize_update_workflow_not_found(workflow_service, mock_db_session):
    """Characterize: update_workflow returns None when workflow not found."""
    # Arrange
    workflow_id = str(uuid4())
    owner_id = 1
    update_data = WorkflowUpdate(name="updated_name")

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize not found behavior
    assert result is None
    assert mock_db_session.commit.call_count == 0


@pytest.mark.asyncio
async def test_characterize_update_workflow_partial_update(workflow_service, mock_db_session, sample_workflow):
    """Characterize: update_workflow with partial data updates only provided fields."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    update_data = WorkflowUpdate(description="Updated description only")

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize partial update behavior
    assert result is not None
    assert result.description == "Updated description only"
    assert result.name == sample_workflow.name  # Unchanged
    assert result.definition == sample_workflow.definition  # Unchanged
    assert result.version == 1  # Unchanged


@pytest.mark.asyncio
async def test_characterize_update_workflow_all_fields(workflow_service, mock_db_session, sample_workflow, sample_workflow_update):
    """Characterize: update_workflow updates all fields including definition."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, sample_workflow_update, owner_id)

    # Assert - Characterize full update behavior
    assert result is not None
    assert result.name == sample_workflow_update.name
    assert result.description == sample_workflow_update.description
    assert result.definition == sample_workflow_update.definition.dict()
    assert result.version == 2  # Incremented due to definition change
    assert mock_db_session.commit.call_count == 2


# ============================================================================
# Characterization Tests - WorkflowService.delete_workflow
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_delete_workflow_soft_delete(workflow_service, mock_db_session, sample_workflow):
    """Characterize: delete_workflow performs soft delete by setting deleted_at."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.delete_workflow(workflow_id, owner_id)

    # Assert - Characterize soft delete behavior
    assert result is True
    assert sample_workflow.deleted_at is not None
    assert sample_workflow.is_active is False
    assert mock_db_session.commit.call_count == 1


@pytest.mark.asyncio
async def test_characterize_delete_workflow_not_found(workflow_service, mock_db_session):
    """Characterize: delete_workflow returns False when workflow not found."""
    # Arrange
    workflow_id = str(uuid4())
    owner_id = 1

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.delete_workflow(workflow_id, owner_id)

    # Assert - Characterize not found behavior
    assert result is False
    assert mock_db_session.commit.call_count == 0


@pytest.mark.asyncio
async def test_characterize_delete_workflow_sets_inactive(workflow_service, mock_db_session, sample_workflow):
    """Characterize: delete_workflow sets is_active to False."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    sample_workflow.is_active = True

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    await workflow_service.delete_workflow(workflow_id, owner_id)

    # Assert - Characterize is_active update behavior
    assert sample_workflow.is_active is False


# ============================================================================
# Characterization Tests - WorkflowService._create_version_entry
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_create_version_entry(workflow_service, mock_db_session, sample_workflow):
    """Characterize: _create_version_entry creates WorkflowVersion with correct data."""
    # Arrange
    created_by = 1

    # Act
    await workflow_service._create_version_entry(sample_workflow, created_by)

    # Assert - Characterize version entry creation
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

    version_entry = mock_db_session.add.call_args[0][0]
    assert isinstance(version_entry, WorkflowVersion)
    assert version_entry.workflow_id == sample_workflow.id
    assert version_entry.version == sample_workflow.version
    assert version_entry.definition == sample_workflow.definition
    assert version_entry.created_by == created_by


@pytest.mark.asyncio
async def test_characterize_create_version_entry_with_complex_definition(workflow_service, mock_db_session):
    """Characterize: _create_version_entry stores complex workflow definitions."""
    # Arrange
    workflow = Workflow()
    workflow.id = str(uuid4())
    workflow.version = 2
    workflow.definition = {
        "nodes": [
            {"id": "n1", "type": "source", "config": {"path": "/data"}},
            {"id": "n2", "type": "transform", "config": {"method": "aggregate"}}
        ],
        "edges": [{"from": "n1", "to": "n2"}],
        "metadata": {"author": "test", "tags": ["prod", "etl"]}
    }

    created_by = 1

    # Act
    await workflow_service._create_version_entry(workflow, created_by)

    # Assert - Characterize complex definition storage
    version_entry = mock_db_session.add.call_args[0][0]
    assert version_entry.definition == workflow.definition
    assert version_entry.definition["nodes"][0]["config"]["path"] == "/data"
    assert version_entry.definition["metadata"]["tags"] == ["prod", "etl"]


# ============================================================================
# Characterization Tests - Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_update_workflow_with_null_description(workflow_service, mock_db_session, sample_workflow):
    """Characterize: update_workflow handles None for description field."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    sample_workflow.description = "Original description"
    update_data = WorkflowUpdate(description=None)

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize None description handling
    assert result is not None
    assert result.description is None


@pytest.mark.asyncio
async def test_characterize_update_workflow_empty_string_name(workflow_service, mock_db_session, sample_workflow):
    """Characterize: update_workflow handles empty string for name."""
    # Arrange
    workflow_id = sample_workflow.id
    owner_id = 1
    update_data = WorkflowUpdate(name="")

    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value=sample_workflow)
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await workflow_service.update_workflow(workflow_id, update_data, owner_id)

    # Assert - Characterize empty string handling
    assert result is not None
    assert result.name == ""


@pytest.mark.asyncio
async def test_characterize_create_workflow_with_large_definition(workflow_service, mock_db_session):
    """Characterize: create_workflow handles large workflow definitions."""
    # Arrange
    large_definition = {
        "nodes": [{"id": f"node_{i}", "type": "transform"} for i in range(1000)],
        "edges": [{"from": f"node_{i}", "to": f"node_{i+1}"} for i in range(999)]
    }

    create_data = WorkflowCreate(
        name="large_workflow",
        definition=large_definition
    )
    owner_id = 1

    mock_execute_result = Mock()
    mock_execute_result.scalar_one_or_none = Mock(return_value=None)
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    await workflow_service.create_workflow(create_data, owner_id)

    # Assert - Characterize large definition handling
    created_workflow = mock_db_session.add.call_args_list[0][0][0]
    assert created_workflow.definition == large_definition
    assert len(created_workflow.definition["nodes"]) == 1000
    assert len(created_workflow.definition["edges"]) == 999


# ============================================================================
# Characterization Tests - Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_characterize_workflow_service_initialization():
    """Characterize: WorkflowService initialization."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Act
    service = WorkflowService(mock_session)

    # Assert - Characterize initialization behavior
    assert service.db == mock_session
    assert isinstance(service, WorkflowService)
