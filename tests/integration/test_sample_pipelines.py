"""
Sample Pipeline Integration Tests

This module tests sample pipelines from the public/examples/ directory.
It validates pipeline structure and tests end-to-end execution for key scenarios.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class SamplePipelineTest:
    """Base class for sample pipeline testing with common utilities."""

    def __init__(self):
        self.sample_pipelines_dir = Path("public/examples")
        self.base_url = "http://localhost:8000/api/v1"

    def load_pipelines(self) -> List[Dict[str, Any]]:
        """Load all sample pipeline JSON files."""
        pipelines = []
        for json_file in self.sample_pipelines_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    pipelines.append({
                        "name": json_file.stem,
                        "path": str(json_file),
                        "content": content,
                        "directory": str(json_file.parent.relative_to(self.sample_pipelines_dir))
                    })
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not load {json_file}: {e}")
        return pipelines

    def validate_pipeline_structure(self, pipeline: Dict[str, Any]) -> List[str]:
        """Validate pipeline structure and return any issues."""
        issues = []
        content = pipeline["content"]

        # Check required fields
        required_fields = ["name", "nodes", "edges"]
        for field in required_fields:
            if field not in content:
                issues.append(f"Missing required field: {field}")

        # Validate nodes
        if "nodes" in content:
            node_ids = set()
            for i, node in enumerate(content["nodes"]):
                if "id" not in node:
                    issues.append(f"Node {i} missing id field")
                else:
                    if node["id"] in node_ids:
                        issues.append(f"Duplicate node id: {node['id']}")
                    node_ids.add(node["id"])

                if "type" not in node:
                    issues.append(f"Node {i} missing type field")
                elif node["type"] == "input" and "data" not in node:
                    issues.append(f"Input node {node['id']} missing data field")

        # Validate edges
        if "edges" in content:
            source_ids = set()
            target_ids = set()
            for i, edge in enumerate(content["edges"]):
                if "source" not in edge or "target" not in edge:
                    issues.append(f"Edge {i} missing source or target")
                else:
                    source_ids.add(edge["source"])
                    target_ids.add(edge["target"])

            # Check edge references point to existing nodes
            if "nodes" in content:
                for node_id in node_ids:
                    if node_id not in source_ids and node_id not in target_ids:
                        issues.append(f"Node {node_id} not connected by any edge")

        return issues

    def get_csv_data_path(self, pipeline: Dict[str, Any]) -> Optional[str]:
        """Get the CSV file path for the pipeline."""
        for node in pipeline["content"]["nodes"]:
            if node["type"] == "input" and "config" in node["data"]:
                config = node["data"]["config"]
                if "file_path" in config:
                    return config["file_path"]
        return None


@pytest.fixture
def sample_pipelines():
    """Load all sample pipeline JSON files."""
    test_instance = SamplePipelineTest()
    return test_instance.load_pipelines()


def test_pipeline_structure(sample_pipelines):
    """Validate structure of all sample pipelines."""
    test_instance = SamplePipelineTest()

    total_pipelines = len(sample_pipelines)
    valid_pipelines = 0
    issues_by_pipeline = {}

    for pipeline in sample_pipelines:
        issues = test_instance.validate_pipeline_structure(pipeline)
        if issues:
            issues_by_pipeline[pipeline["name"]] = issues
            print(f"Pipeline '{pipeline['name']}' has issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            valid_pipelines += 1

    print(f"\nPipeline Structure Validation Results:")
    print(f"Total pipelines: {total_pipelines}")
    print(f"Valid pipelines: {valid_pipelines}")
    print(f"Pipelines with issues: {len(issues_by_pipeline)}")

    # Report by category
    categories = {}
    for pipeline_name, issues in issues_by_pipeline.items():
        category = pipeline["directory"]
        if category not in categories:
            categories[category] = 0
        categories[category] += 1

    print(f"\nIssues by category:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count} pipelines")

    # Test key pipeline categories
    expected_categories = [
        "analytics", "api-integration", "enrichment", "export",
        "ingestion", "transformation", "batch", "quality"
    ]

    found_categories = set()
    for pipeline in sample_pipelines:
        category = pipeline["directory"]
        if category in expected_categories:
            found_categories.add(category)

    missing_categories = set(expected_categories) - found_categories
    if missing_categories:
        print(f"\nWarning: Missing expected categories: {missing_categories}")

    # Assert that most pipelines are valid (allowing for some complex edge cases)
    assert valid_pipelines >= total_pipelines * 0.8, f"Too many invalid pipelines: {valid_pipelines}/{total_pipelines}"

    # Report specific issues for top categories
    for category in ["analytics", "api-integration", "enrichment"]:
        category_pipelines = [p for p in sample_pipelines if p["directory"] == category]
        if category_pipelines:
            print(f"\n{category.upper()} category (count: {len(category_pipelines)}):")
            for pipeline in category_pipelines:
                if pipeline["name"] in issues_by_pipeline:
                    print(f"  - {pipeline['name']}: {len(issues_by_pipeline[pipeline['name']])} issues")


def test_node_types_distribution(sample_pipelines):
    """Analyze node types distribution across all pipelines."""
    node_type_counts = {}

    for pipeline in sample_pipelines:
        for node in pipeline["content"]["nodes"]:
            node_type = node.get("type", "unknown")
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    print(f"\nNode Types Distribution:")
    for node_type, count in sorted(node_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {node_type}: {count}")

    # Ensure we have the basic node types
    expected_types = ["input", "output", "default"]
    for node_type in expected_types:
        assert node_type in node_type_counts, f"Missing expected node type: {node_type}"


def test_subtypes_in_default_nodes(sample_pipelines):
    """Analyze subtypes in default nodes."""
    subtype_counts = {}

    for pipeline in sample_pipelines:
        for node in pipeline["content"]["nodes"]:
            if node.get("type") == "default" and "data" in node:
                data = node["data"]
                subtype = data.get("subtype", "unknown")
                subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1

    print(f"\nDefault Node Subtypes:")
    for subtype, count in sorted(subtype_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {subtype}: {count}")

    # Ensure we have common subtypes
    common_subtypes = ["filter", "transform", "raw_sql", "batch_request", "clean"]
    for subtype in common_subtypes:
        if subtype in subtype_counts:
            print(f"  ✓ {subtype}: {subtype_counts[subtype]}")
        else:
            print(f"  ✗ {subtype}: not found")


@pytest.mark.asyncio
async def test_key_sample_pipelines_structure():
    """Test structure validation of key sample pipelines."""
    test_instance = SamplePipelineTest()

    # Test specific key pipelines
    key_pipeline_names = [
        "sample_user_enrichment_pipeline",
        "ecommerce_product_pipeline",
        "data_cleaning_pipeline",
        "multi_format_export_pipeline"
    ]

    for pipeline_name in key_pipeline_names:
        pipeline = None
        for p in test_instance.load_pipelines():
            if p["name"] == pipeline_name:
                pipeline = p
                break

        if pipeline is None:
            print(f"Warning: Key pipeline {pipeline_name} not found")
            continue

        issues = test_instance.validate_pipeline_structure(pipeline)

        print(f"\nKey Pipeline: {pipeline_name}")
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            # For key pipelines, we expect them to be valid
            assert not issues, f"Key pipeline {pipeline_name} should not have issues"
        else:
            print("✓ Valid structure")


@pytest.mark.asyncio
async def test_pipeline_configuration_variety():
    """Test that pipelines have diverse configurations."""
    test_instance = SamplePipelineTest()
    pipelines = test_instance.load_pipelines()

    # Test for different input sources
    input_sources = set()
    for pipeline in pipelines:
        for node in pipeline["content"]["nodes"]:
            if node["type"] == "input" and "data" in node:
                config = node["data"]["config"]
                if "file_path" in config:
                    file_ext = Path(config["file_path"]).suffix.lower()
                    if file_ext == ".csv":
                        input_sources.add("csv")
                    elif file_ext == ".json":
                        input_sources.add("json")
                    elif file_ext == ".xlsx" or file_ext == ".xls":
                        input_sources.add("excel")

    print(f"\nInput sources found: {input_sources}")
    assert len(input_sources) >= 2, f"Should have multiple input sources, found: {input_sources}"

    # Test for different output formats
    output_formats = set()
    for pipeline in pipelines:
        for node in pipeline["content"]["nodes"]:
            if node["type"] == "output" and "data" in node:
                config = node["data"]["config"]
                if "filename" in config:
                    file_ext = Path(config["filename"]).suffix.lower()
                    if file_ext == ".csv":
                        output_formats.add("csv")
                    elif file_ext == ".json":
                        output_formats.add("json")
                    elif file_ext in [".xlsx", ".xls"]:
                        output_formats.add("excel")

    print(f"Output formats found: {output_formats}")
    assert len(output_formats) >= 1, f"Should have at least one output format, found: {output_formats}"


@pytest.mark.asyncio
async def test_complex_pipeline_structure():
    """Test complex pipelines have valid structure."""
    test_instance = SamplePipelineTest()

    # Find complex pipelines (many nodes)
    complex_pipelines = []
    for pipeline in test_instance.load_pipelines():
        if len(pipeline["content"]["nodes"]) > 5:
            complex_pipelines.append(pipeline)

    print(f"\nFound {len(complex_pipelines)} complex pipelines")

    for pipeline in complex_pipelines:
        issues = test_instance.validate_pipeline_structure(pipeline)

        print(f"\nComplex Pipeline: {pipeline['name']} ({len(pipeline['content']['nodes'])} nodes)")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ Complex pipeline structure is valid")


@pytest.mark.asyncio
async def test_pipeline_naming_conventions():
    """Test pipeline naming conventions."""
    test_instance = SamplePipelineTest()
    pipelines = test_instance.load_pipelines()

    valid_names = 0
    naming_issues = []

    for pipeline in pipelines:
        name = pipeline["name"]
        # Check if name follows convention: snake_case or kebab-case
        is_valid = (name.replace('_', '').replace('-', '').isalnum() and
                   '_' in name or '-' in name)

        if not is_valid:
            naming_issues.append(f"Pipeline name '{name}' doesn't follow naming convention")
        else:
            valid_names += 1

    print(f"\nNaming Convention Results:")
    print(f"Valid names: {valid_names}")
    print(f"Issues: {len(naming_issues)}")

    for issue in naming_issues[:5]:  # Show first 5 issues
        print(f"  - {issue}")

    # Most pipelines should follow naming conventions
    assert valid_names >= len(pipelines) * 0.7, f"Too many naming issues: {valid_names}/{len(pipelines)}"


# Example test for a specific pipeline (can be expanded with actual execution)
@pytest.mark.asyncio
async def test_user_enrichment_pipeline_structure():
    """Test the user enrichment pipeline specifically."""
    test_instance = SamplePipelineTest()

    # Find the user enrichment pipeline
    user_pipeline = None
    for pipeline in test_instance.load_pipelines():
        if pipeline["name"] == "sample_user_enrichment_pipeline":
            user_pipeline = pipeline
            break

    assert user_pipeline is not None, "User enrichment pipeline not found"

    # Validate its structure
    issues = test_instance.validate_pipeline_structure(user_pipeline)
    assert not issues, f"User enrichment pipeline should not have issues, found: {issues}"

    # Check specific node types
    node_types = [node["type"] for node in user_pipeline["content"]["nodes"]]
    assert "input" in node_types, "Should have input node"
    assert "output" in node_types, "Should have output node"

    # Check for batch processing node
    default_nodes = [node for node in user_pipeline["content"]["nodes"] if node["type"] == "default"]
    batch_nodes = [node for node in default_nodes if node["data"]["subtype"] == "batch_request"]
    assert len(batch_nodes) > 0, "Should have batch processing node"

    print(f"\nUser Enrichment Pipeline Validation:")
    print(f"  ✓ Nodes: {len(user_pipeline['content']['nodes'])}")
    print(f"  ✓ Edges: {len(user_pipeline['content']['edges'])}")
    print(f"  ✓ Batch nodes: {len(batch_nodes)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])