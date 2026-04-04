---
name: workflow-validator
description: Validate workflow JSON schemas for DuckDB workflow builder, ensure structural integrity, and create reference workflow configurations for E2E testing. Verify node types, edge connections, configuration parameters, and workflow execution. Use when: user mentions "workflow validation", "workflow JSON", "workflow schema", "workflow testing", "reference workflows", "workflow examples" for E2E testing, workflow configuration validation. DOES NOT trigger for: general JSON validation, schema validation without workflow context, workflow execution without validation.
---

# Workflow Validator Skill

Validate workflow JSON schemas, ensure structural integrity, and create reference workflow configurations for E2E testing.

## Your Responsibilities

1. **Validate Workflow JSON**: Ensure all workflows are structurally valid
2. **Create Reference Workflows**: Generate example workflows for each node type
3. **Document Schemas**: Specify node configurations and parameters
4. **Verify Execution**: Test workflow execution produces expected results
5. **Flag Issues**: Report invalid workflows with specific error details

## Workflow Schema

### Basic Structure
```json
{
  "nodes": [
    {
      "id": "string",
      "type": "input|filter|aggregate|join|sql|output",
      "position": { "x": number, "y": number },
      "data": {
        "label": "string",
        "rowCount": number,
        "config": {}
      }
    }
  ],
  "edges": [
    {
      "id": "string",
      "source": "node_id",
      "target": "node_id",
      "type": "default"
    }
  ]
}
```

## Node Type Schemas

### Input Node
```json
{
  "id": "input-1",
  "type": "input",
  "position": { "x": 100, "y": 100 },
  "data": {
    "label": "Upload CSV",
    "config": {
      "fileName": "test_data_diverse.csv",
      "delimiter": ",",
      "hasHeader": true
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`
**Optional Fields**: `data.rowCount`, `data.config`

### Filter Node
```json
{
  "id": "filter-1",
  "type": "filter",
  "position": { "x": 100, "y": 300 },
  "data": {
    "label": "Filter: amount > 1000",
    "config": {
      "condition": "amount > 1000"
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`, `data.config.condition`

### Aggregate Node
```json
{
  "id": "aggregate-1",
  "type": "aggregate",
  "position": { "x": 100, "y": 500 },
  "data": {
    "label": "Group by account_type",
    "config": {
      "groupBy": ["account_type"],
      "aggregations": [
        { "column": "amount", "function": "sum", "alias": "total_amount" },
        { "column": "txn_id", "function": "count", "alias": "transaction_count" }
      ]
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`, `data.config.groupBy`, `data.config.aggregations`

### Join Node
```json
{
  "id": "join-1",
  "type": "join",
  "position": { "x": 400, "y": 300 },
  "data": {
    "label": "Join account types",
    "config": {
      "joinType": "left",
      "joinKeys": {
        "left": "account_type",
        "right": "account_type"
      }
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`, `data.config.joinType`, `data.config.joinKeys`

### SQL Node
```json
{
  "id": "sql-1",
  "type": "sql",
  "position": { "x": 100, "y": 700 },
  "data": {
    "label": "Custom SQL",
    "config": {
      "query": "SELECT account_type, SUM(amount) as total FROM data GROUP BY account_type"
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`, `data.config.query`

### Output Node
```json
{
  "id": "output-1",
  "type": "output",
  "position": { "x": 100, "y": 900 },
  "data": {
    "label": "Results",
    "config": {
      "exportFormat": "csv",
      "fileName": "output.csv"
    }
  }
}
```

**Required Fields**: `id`, `type`, `position`, `data.label`
**Optional Fields**: `data.config.exportFormat`, `data.config.fileName`

## Validation Checks

### 1. Structural Validation
- [ ] JSON is valid (parseable)
- [ ] Root has `nodes` array and `edges` array
- [ ] All nodes have required fields
- [ ] All edges have `id`, `source`, `target`

### 2. Node Type Validation
- [ ] All `type` values are valid node types
- [ ] Each node has correct configuration for its type
- [ ] Required config fields are present
- [ ] Config values are correct data types

### 3. Edge Validation
- [ ] All edge `source` IDs reference existing nodes
- [ ] All edge `target` IDs reference existing nodes
- [ ] No self-loops (source == target)
- [ ] No duplicate edges

### 4. Flow Validation
- [ ] Workflow has at least one input node
- [ ] Workflow has at least one output node (optional)
- [ ] All nodes are reachable from input (no disconnected nodes)
- [ ] No circular dependencies

### 5. Semantic Validation
- [ ] Filter conditions are valid SQL WHERE clauses
- [ ] Aggregate groupBy columns exist
- [ ] SQL queries are syntactically valid
- [ ] Join keys reference valid columns

## Reference Workflow Templates

### Smoke Test Workflow
```json
{
  "nodes": [
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "Upload CSV" }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 100, "y": 300 },
      "data": { "label": "Results" }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "input-1",
      "target": "output-1"
    }
  ]
}
```

### Filter Workflow
```json
{
  "nodes": [
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "Upload CSV" }
    },
    {
      "id": "filter-1",
      "type": "filter",
      "position": { "x": 100, "y": 300 },
      "data": {
        "label": "Filter: amount > 1000",
        "config": { "condition": "amount > 1000" }
      }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 100, "y": 500 },
      "data": { "label": "Results" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "input-1", "target": "filter-1" },
    { "id": "e2", "source": "filter-1", "target": "output-1" }
  ]
}
```

### Aggregate Workflow
```json
{
  "nodes": [
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "Upload CSV" }
    },
    {
      "id": "aggregate-1",
      "type": "aggregate",
      "position": { "x": 100, "y": 300 },
      "data": {
        "label": "Group by account_type",
        "config": {
          "groupBy": ["account_type"],
          "aggregations": [
            { "column": "amount", "function": "sum", "alias": "total_amount" }
          ]
        }
      }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 100, "y": 500 },
      "data": { "label": "Results" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "input-1", "target": "aggregate-1" },
    { "id": "e2", "source": "aggregate-1", "target": "output-1" }
  ]
}
```

### Join Workflow
```json
{
  "nodes": [
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "Main Data" }
    },
    {
      "id": "input-2",
      "type": "input",
      "position": { "x": 400, "y": 100 },
      "data": { "label": "Join Data" }
    },
    {
      "id": "join-1",
      "type": "join",
      "position": { "x": 250, "y": 300 },
      "data": {
        "label": "Join Tables",
        "config": {
          "joinType": "inner",
          "joinKeys": {
            "left": "account_type",
            "right": "account_type"
          }
        }
      }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 250, "y": 500 },
      "data": { "label": "Results" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "input-1", "target": "join-1" },
    { "id": "e2", "source": "input-2", "target": "join-1" },
    { "id": "e3", "source": "join-1", "target": "output-1" }
  ]
}
```

### SQL Workflow
```json
{
  "nodes": [
    {
      "id": "input-1",
      "type": "input",
      "position": { "x": 100, "y": 100 },
      "data": { "label": "Upload CSV" }
    },
    {
      "id": "sql-1",
      "type": "sql",
      "position": { "x": 100, "y": 300 },
      "data": {
        "label": "Custom Query",
        "config": {
          "query": "SELECT account_type, COUNT(*) as count FROM data GROUP BY account_type"
        }
      }
    },
    {
      "id": "output-1",
      "type": "output",
      "position": { "x": 100, "y": 500 },
      "data": { "label": "Results" }
    }
  ],
  "edges": [
    { "id": "e1", "source": "input-1", "target": "sql-1" },
    { "id": "e2", "source": "sql-1", "target": "output-1" }
  ]
}
```

## Implementation Steps

1. **Review Workflows**: Read all `/data/workflows/*.json` files
2. **Validate Structure**: Check JSON syntax and required fields
3. **Validate Types**: Verify node types and configurations
4. **Validate Edges**: Check edge references and connections
5. **Create References**: Generate reference workflows for each node type
6. **Document Schemas**: Write schema documentation
7. **Report Issues**: Flag invalid workflows with specific errors

## File Output

### Validated Workflows
- **Path**: `/data/workflows/validation/{workflow_name}_validated.json`
- **Content**: Validated workflow JSON with validation report

### Schema Documentation
- **Path**: `/docs/workflow_schema.md`
- **Content**: Complete schema specification for all node types

### Validation Report
- **Path**: `/tests/e2e/validation_report.md`
- **Content**: Pass/fail status for all workflows, issues found

### Reference Workflows
- **Path**: `/data/workflows/reference/{node_type}_workflow.json`
- **Content**: Example workflow for each node type

## Quality Checks

Before finalizing validation:
- [ ] All workflows are structurally valid
- [ ] All node configurations are correct
- [ ] All edge references are valid
- [ ] Schema documentation is complete
- [ ] Reference workflows are created
- [ ] Validation report is generated

## Error Handling

**If workflow JSON is invalid:**
- Log specific validation error (line number, field name, expected value)
- Suggest fix based on error type
- Continue with remaining workflows
- Flag for manual review

**If schema is incomplete:**
- Document missing fields
- Create placeholder schema with `// TODO: document this field`
- Flag gaps for manual review
- Suggest improvements to product documentation

**If workflow execution fails:**
- Capture error details (error message, stack trace)
- Verify if it's expected failure (negative test)
- Check if it's data issue vs workflow issue
- Document actual vs expected behavior

## Communication Protocol

**Send To:**
- **e2e-automation-engineer**: Validated workflow JSON, schema documentation
- **test-case-strategist**: Workflow feasibility feedback, config options
- **e2e-orchestrator**: Validation completion, issues found

**Receive From:**
- **test-case-strategist**: Workflow requirements for test scenarios
- **test-data-architect**: Test data compatibility requirements
- **e2e-orchestrator**: Validation task assignments

## Why This Matters

Valid workflow JSONs are critical for reliable E2E testing. Invalid workflows cause test failures that aren't bugs but configuration errors. Proper validation ensures:

1. **Test Reliability**: Valid workflows prevent false-negative test failures
2. **Clear Documentation**: Schema docs help understand configuration options
3. **Efficient Debugging**: Known-good reference workflows simplify troubleshooting
4. **Onboarding**: Reference workflows help new developers understand the system
