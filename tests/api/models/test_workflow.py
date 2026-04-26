"""
Characterization tests for Workflow model.

These tests capture the CURRENT BEHAVIOR of the Workflow model
to serve as a safety net during refactoring in the IMPROVE phase.

@MX:NOTE: Characterization tests document actual behavior, not intended behavior
@MX:SPEC: SPEC-WORKFLOW-001
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.api.models.workflow import Workflow
from src.api.models.base import BaseModel


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_workflow_data():
    """Sample workflow data for testing."""
    return {
        "name": "test_workflow",
        "description": "Test workflow for characterization",
        "definition": {
            "nodes": [
                {"id": "node1", "type": "source"},
                {"id": "node2", "type": "transform"}
            ],
            "edges": [
                {"from": "node1", "to": "node2"}
            ]
        },
        "owner_id": 1,
        "is_active": True,
        "version": 1
    }


# ============================================================================
# Characterization Tests - Workflow Model
# ============================================================================

def test_characterize_workflow_creation(sample_workflow_data):
    """Characterize: Workflow creation sets all fields correctly."""
    # Arrange & Act
    workflow = Workflow(**sample_workflow_data)

    # Assert - Characterize actual behavior
    assert workflow.name == sample_workflow_data["name"]
    assert workflow.description == sample_workflow_data["description"]
    assert workflow.definition == sample_workflow_data["definition"]
    assert workflow.owner_id == sample_workflow_data["owner_id"]
    assert workflow.is_active == sample_workflow_data["is_active"]
    assert workflow.version == sample_workflow_data["version"]

    # Characterize timestamp behavior
    assert hasattr(workflow, "created_at")
    assert hasattr(workflow, "updated_at")


def test_characterize_workflow_repr(sample_workflow_data):
    """Characterize: Workflow __repr__ output format."""
    # Arrange
    workflow = Workflow(**sample_workflow_data)
    workflow.id = 1

    # Act
    repr_str = repr(workflow)

    # Assert - Characterize actual repr format
    assert "Workflow" in repr_str
    assert "id=1" in repr_str
    assert f"name={workflow.name}" in repr_str
    assert f"version={workflow.version}" in repr_str


def test_characterize_workflow_to_dict(sample_workflow_data):
    """Characterize: Workflow to_dict() includes definition."""
    # Arrange
    workflow = Workflow(**sample_workflow_data)
    workflow.id = 1

    # Act
    workflow_dict = workflow.to_dict()

    # Assert - Characterize actual dict structure
    assert isinstance(workflow_dict, dict)
    assert "id" in workflow_dict
    assert "name" in workflow_dict
    assert "description" in workflow_dict
    assert "definition" in workflow_dict
    assert workflow_dict["definition"] == sample_workflow_data["definition"]


def test_characterize_workflow_default_values():
    """Characterize: Workflow field default values."""
    # Arrange - Minimal workflow data
    minimal_data = {
        "name": "minimal_workflow",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**minimal_data)

    # Assert - Characterize default behavior
    assert workflow.version == 1  # Default version
    assert workflow.is_active == True  # Default active status
    assert workflow.description is None  # Optional field


def test_characterize_workflow_json_field_type():
    """Characterize: Workflow definition field stores JSON data."""
    # Arrange
    complex_definition = {
        "nodes": [
            {
                "id": "node1",
                "type": "source",
                "config": {"path": "/data/input"}
            }
        ],
        "edges": [],
        "metadata": {
            "author": "test_user",
            "tags": ["etl", "production"]
        }
    }

    workflow_data = {
        "name": "complex_workflow",
        "definition": complex_definition,
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize JSON storage behavior
    assert workflow.definition == complex_definition
    assert isinstance(workflow.definition, dict)
    assert workflow.definition["nodes"][0]["config"]["path"] == "/data/input"
    assert workflow.definition["metadata"]["tags"] == ["etl", "production"]


def test_characterize_workflow_string_fields():
    """Characterize: Workflow string field constraints."""
    # Arrange - Test with various string lengths
    long_name = "a" * 255  # Max length for name field
    long_description = "a" * 10000  # Long description (Text field)

    workflow_data = {
        "name": long_name,
        "description": long_description,
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize string field behavior
    assert len(workflow.name) == 255
    assert len(workflow.description) == 10000


def test_characterize_workflow_nullability():
    """Characterize: Workflow field nullability constraints."""
    # Arrange - Test with nullable fields set to None
    workflow_data = {
        "name": "nullable_test",
        "description": None,  # Nullable field
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize null behavior
    assert workflow.description is None
    assert workflow.name == "nullable_test"  # Required field


# ============================================================================
# Characterization Tests - Workflow Relationships
# ============================================================================

def test_characterize_workflow_relationships_exist(sample_workflow_data):
    """Characterize: Workflow has relationship attributes defined."""
    # Arrange
    workflow = Workflow(**sample_workflow_data)

    # Assert - Characterize relationship configuration
    assert hasattr(workflow, "owner")
    assert hasattr(workflow, "jobs")
    assert hasattr(workflow, "versions")

    # Characterize relationship types
    from sqlalchemy.orm import relationships
    assert isinstance(workflow.__class__.owner.property, relationships.RelationshipProperty)
    assert isinstance(workflow.__class__.jobs.property, relationships.RelationshipProperty)
    assert isinstance(workflow.__class__.versions.property, relationships.RelationshipProperty)


# ============================================================================
# Characterization Tests - Workflow Constraints
# ============================================================================

def test_characterize_workflow_primary_key_type():
    """Characterize: Workflow uses Integer primary key from BaseModel."""
    # Arrange
    workflow_data = {
        "name": "test_workflow",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize primary key behavior
    from sqlalchemy import Integer
    assert isinstance(workflow.__class__.id.type, Integer)


def test_characterize_workflow_version_initial_value():
    """Characterize: Workflow version starts at 1 for new workflows."""
    # Arrange
    workflow_data = {
        "name": "version_test",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize initial version behavior
    assert workflow.version == 1


def test_characterize_workflow_active_status_default():
    """Characterize: Workflow is_active defaults to True."""
    # Arrange
    workflow_data = {
        "name": "active_test",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize default active status
    assert workflow.is_active is True


# ============================================================================
# Characterization Tests - Workflow Inheritance
# ============================================================================

def test_characterize_workflow_inherits_from_base_model():
    """Characterize: Workflow inherits BaseModel fields."""
    # Arrange
    workflow_data = {
        "name": "inheritance_test",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize BaseModel inheritance
    assert isinstance(workflow, BaseModel)
    assert hasattr(workflow, "id")
    assert hasattr(workflow, "created_at")
    assert hasattr(workflow, "updated_at")
    assert hasattr(workflow, "deleted_at")


# ============================================================================
# Characterization Tests - Edge Cases
# ============================================================================

def test_characterize_workflow_empty_definition():
    """Characterize: Workflow behavior with empty definition."""
    # Arrange
    workflow_data = {
        "name": "empty_definition_test",
        "definition": {},  # Empty definition
        "owner_id": 1
    }

    # Act
    workflow = Workflow(**workflow_data)

    # Assert - Characterize empty definition behavior
    assert workflow.definition == {}
    assert isinstance(workflow.definition, dict)


def test_characterize_workflow_special_characters_in_name():
    """Characterize: Workflow handles special characters in name."""
    # Arrange
    special_names = [
        "workflow-with-dashes",
        "workflow_with_underscores",
        "workflow.with.dots",
        "workflow with spaces",
        "工作流",  # Non-ASCII characters
    ]

    # Act
    workflows = []
    for name in special_names:
        workflow_data = {
            "name": name,
            "definition": {"nodes": [], "edges": []},
            "owner_id": 1
        }
        workflow = Workflow(**workflow_data)
        workflows.append(workflow)

    # Assert - Characterize special character handling
    for i, workflow in enumerate(workflows):
        assert workflow.name == special_names[i]


# ============================================================================
# Characterization Tests - BaseModel Behavior
# ============================================================================

def test_characterize_workflow_base_model_to_dict():
    """Characterize: Workflow inherits to_dict from BaseModel."""
    # Arrange
    workflow_data = {
        "name": "to_dict_test",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }
    workflow = Workflow(**workflow_data)
    workflow.id = 1

    # Act
    workflow_dict = workflow.to_dict()

    # Assert - Characterize BaseModel to_dict behavior
    assert "id" in workflow_dict
    assert "created_at" in workflow_dict
    assert "updated_at" in workflow_dict
    assert "deleted_at" in workflow_dict


def test_characterize_workflow_base_model_is_deleted():
    """Characterize: Workflow inherits is_deleted from BaseModel."""
    # Arrange
    workflow_data = {
        "name": "is_deleted_test",
        "definition": {"nodes": [], "edges": []},
        "owner_id": 1
    }
    workflow = Workflow(**workflow_data)

    # Assert - Characterize is_deleted behavior
    assert hasattr(workflow, "is_deleted")
    assert workflow.is_deleted() == False  # Not deleted by default

    # Act - Mark as deleted
    from datetime import datetime
    workflow.deleted_at = datetime.utcnow()

    # Assert - is_deleted should return True
    assert workflow.is_deleted() == True
