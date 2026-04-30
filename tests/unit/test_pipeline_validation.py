"""
Pipeline Validation Unit Tests

This module tests pipeline validation functions without requiring external services.
"""

import pytest
import json
import tempfile
from pathlib import Path
from tests.integration.test_sample_pipelines import SamplePipelineTest


class TestPipelineValidation:
    """Test pipeline validation functions."""

    def test_basic_pipeline_structure(self):
        """Test basic pipeline structure validation."""
        test_instance = SamplePipelineTest()

        # Valid pipeline
        valid_pipeline = {
            "name": "Test Pipeline",
            "nodes": [
                {"id": "input1", "type": "input", "data": {"config": {"file_path": "test.csv"}}},
                {"id": "transform1", "type": "default", "data": {"subtype": "filter"}},
                {"id": "output1", "type": "output"}
            ],
            "edges": [
                {"id": "e1", "source": "input1", "target": "transform1"},
                {"id": "e2", "source": "transform1", "target": "output1"}
            ]
        }

        issues = test_instance.validate_pipeline_structure({"content": valid_pipeline})
        assert len(issues) == 0, f"Valid pipeline should have no issues, got: {issues}"

    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        test_instance = SamplePipelineTest()

        # Missing required fields
        invalid_pipeline = {
            "name": "Invalid Pipeline"
            # Missing "nodes" and "edges"
        }

        issues = test_instance.validate_pipeline_structure({"content": invalid_pipeline})
        assert len(issues) >= 2, f"Should detect missing required fields, got: {issues}"

    def test_duplicate_node_ids(self):
        """Test detection of duplicate node IDs."""
        test_instance = SamplePipelineTest()

        duplicate_id_pipeline = {
            "name": "Duplicate ID Pipeline",
            "nodes": [
                {"id": "node1", "type": "input"},
                {"id": "node1", "type": "output"}  # Duplicate ID
            ],
            "edges": []
        }

        issues = test_instance.validate_pipeline_structure({"content": duplicate_id_pipeline})
        assert any("Duplicate node id" in issue for issue in issues), f"Should detect duplicate IDs, got: {issues}"

    def test_unconnected_nodes(self):
        """Test detection of unconnected nodes."""
        test_instance = SamplePipelineTest()

        unconnected_pipeline = {
            "name": "Unconnected Pipeline",
            "nodes": [
                {"id": "input1", "type": "input"},
                {"id": "output1", "type": "output"},
                {"id": "isolated", "type": "default"}  # Not connected
            ],
            "edges": [
                {"id": "e1", "source": "input1", "target": "output1"}
            ]
        }

        issues = test_instance.validate_pipeline_structure({"content": unconnected_pipeline})
        assert any("not connected by any edge" in issue for issue in issues), f"Should detect unconnected nodes, got: {issues}"

    def test_input_node_validation(self):
        """Test validation of input nodes."""
        test_instance = SamplePipelineTest()

        # Missing data in input node
        invalid_input_pipeline = {
            "name": "Invalid Input Pipeline",
            "nodes": [
                {"id": "input1", "type": "input"},  # Missing data
                {"id": "output1", "type": "output"}
            ],
            "edges": []
        }

        issues = test_instance.validate_pipeline_structure({"content": invalid_input_pipeline})
        assert any("Input node" in issue and "missing data field" in issue for issue in issues), f"Should detect input node data issues, got: {issues}"

    def test_load_real_pipelines(self):
        """Test loading real pipeline files."""
        test_instance = SamplePipelineTest()
        pipelines = test_instance.load_pipelines()

        assert len(pipelines) > 0, "Should load some pipelines"

        # First pipeline should have required structure
        first_pipeline = pipelines[0]
        assert "name" in first_pipeline["content"]
        assert "nodes" in first_pipeline["content"]
        assert "edges" in first_pipeline["content"]

    def test_node_types_count(self):
        """Test counting node types across real pipelines."""
        test_instance = SamplePipelineTest()
        pipelines = test_instance.load_pipelines()

        node_type_counts = {}

        for pipeline in pipelines:
            for node in pipeline["content"]["nodes"]:
                node_type = node.get("type", "unknown")
                node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

        # Should have basic node types
        assert "input" in node_type_counts, f"Should have input nodes, got: {node_type_counts}"
        assert "output" in node_type_counts, f"Should have output nodes, got: {node_type_counts}"
        assert "default" in node_type_counts, f"Should have default nodes, got: {node_type_counts}"

    def test_pipeline_naming(self):
        """Test pipeline naming conventions."""
        test_instance = SamplePipelineTest()
        pipelines = test_instance.load_pipelines()

        valid_naming_count = 0
        for pipeline in pipelines:
            name = pipeline["name"]
            # Check if name follows reasonable convention (not empty, contains only reasonable chars)
            if (len(name) > 0 and name.replace('_', '').replace('-', '').isalnum() and
                any(char in name for char in ['_', '-'])):
                valid_naming_count += 1

        # Most pipelines should follow reasonable naming
        assert valid_naming_count >= len(pipelines) * 0.5, f"Should have reasonable naming, got {valid_naming_count}/{len(pipelines)}"

    def test_extract_csv_paths(self):
        """Test extracting CSV file paths from pipelines."""
        test_instance = SamplePipelineTest()

        # Pipeline with CSV input
        pipeline_with_csv = {
            "name": "Test CSV Pipeline",
            "nodes": [
                {"id": "input1", "type": "input", "data": {"config": {"file_path": "data/users.csv"}}},
                {"id": "output1", "type": "output"}
            ],
            "edges": []
        }

        pipeline_data = {"content": pipeline_with_csv}
        csv_path = test_instance.get_csv_data_path(pipeline_data)
        assert csv_path == "data/users.csv", f"Should extract CSV path, got: {csv_path}"

        # Pipeline without CSV
        pipeline_without_csv = {
            "name": "Test No CSV Pipeline",
            "nodes": [
                {"id": "output1", "type": "output"}
            ],
            "edges": []
        }

        pipeline_data = {"content": pipeline_without_csv}
        csv_path = test_instance.get_csv_data_path(pipeline_data)
        assert csv_path is None, f"Should return None for no CSV, got: {csv_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])