# Workflow Schema Documentation

This document describes the JSON schema used for workflow definitions in the DuckDB Web Platform.

## Basic Workflow Structure

A workflow is a JSON object containing `nodes` and `edges` that define a data processing pipeline.

```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "preview_limit": 50,      // optional
  "report_config": null     // optional
}
```

## Node Schema

### Common Node Fields

All nodes share these common fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (format: `{type}-{timestamp}`) |
| `type` | string | Yes | Node type: `"input"`, `"output"`, or `"default"` |
| `position` | object | Yes | Canvas position with `x` and `y` coordinates |
| `data` | object | Yes | Node configuration data |
| `measured` | object | No | UI rendering dimensions (width, height) |
| `selected` | boolean | No | Whether node is selected in UI |
| `dragging` | boolean | No | Whether node is being dragged |

### Node Data Structure

```typescript
{
  data: {
    label: string,        // Display name
    subtype?: string,     // For type="default" nodes
    config: {...},        // Node-specific configuration
    rowCount?: number     // Optional row count display
  }
}
```

## Node Types

### 1. Input Node

**Type**: `"input"`

**Config Schema**:
```json
{
  "file": string,           // Original filename
  "file_path": string,      // Path to uploaded file
  "availableColumns": []    // Array of column names
}
```

**Example**:
```json
{
  "id": "input-001",
  "type": "input",
  "position": { "x": 100, "y": 50 },
  "data": {
    "label": "CSV/Excel File",
    "config": {
      "file": "sales.csv",
      "file_path": "uploads/sales.csv",
      "availableColumns": ["id", "product", "quantity", "price"]
    }
  }
}
```

### 2. Output Node

**Type**: `"output"`

**Config Schema**:
```json
{
  "exportFormat": string,   // "csv", "json", etc.
  "fileName": string,       // Output filename
  "availableColumns": []    // Available columns for export
}
```

**Example**:
```json
{
  "id": "output-001",
  "type": "output",
  "position": { "x": 100, "y": 300 },
  "data": {
    "label": "Export File",
    "config": {
      "exportFormat": "csv",
      "fileName": "output.csv",
      "availableColumns": ["id", "product", "quantity"]
    }
  }
}
```

### 3. Filter Node (Default Type)

**Type**: `"default"`
**Subtype**: `"filter"`

**Config Schema**:
```json
{
  "column": string,          // Column to filter on
  "operator": string,        // ">", "<", "=", "!=", "contains", "not_contains"
  "value": string,           // Filter value
  "availableColumns": [],    // Available columns
  "isAdvanced": boolean      // Whether advanced mode is used
}
```

**Example**:
```json
{
  "id": "filter-001",
  "type": "default",
  "position": { "x": 100, "y": 200 },
  "data": {
    "label": "Filter Records",
    "subtype": "filter",
    "config": {
      "column": "quantity",
      "operator": ">",
      "value": "10",
      "availableColumns": ["id", "product", "quantity", "price"]
    }
  }
}
```

### 4. Aggregate Node (Default Type)

**Type**: `"default"`
**Subtype**: `"aggregate"`

**Config Schema**:
```json
{
  "groupBy": string,         // Column to group by
  "column": string,          // Column to aggregate
  "alias": string,           // Result column name
  "availableColumns": []     // Result columns
}
```

**Example**:
```json
{
  "id": "aggregate-001",
  "type": "default",
  "position": { "x": 100, "y": 200 },
  "data": {
    "label": "Aggregate Data",
    "subtype": "aggregate",
    "config": {
      "groupBy": "category",
      "column": "amount",
      "alias": "total_amount",
      "availableColumns": ["category", "total_amount"]
    }
  }
}
```

### 5. Raw SQL Node (Default Type)

**Type**: `"default"`
**Subtype**: `"raw_sql"`

**Config Schema**:
```json
{
  "sql": string,             // SQL query (use {{input}} for table reference)
  "availableColumns": []     // Result columns
}
```

**Example**:
```json
{
  "id": "sql-001",
  "type": "default",
  "position": { "x": 100, "y": 200 },
  "data": {
    "label": "Custom SQL",
    "subtype": "raw_sql",
    "config": {
      "sql": "SELECT department, AVG(salary) as avg_salary FROM {{input}} GROUP BY department",
      "availableColumns": ["department", "avg_salary"]
    }
  }
}
```

### 6. Sort Node (Default Type)

**Type**: `"default"`
**Subtype**: `"sort"`

**Config Schema**:
```json
{
  "column": string,          // Column to sort by
  "direction": string,       // "asc" or "desc"
  "availableColumns": []     // Available columns
}
```

**Example**:
```json
{
  "id": "sort-001",
  "type": "default",
  "position": { "x": 100, "y": 200 },
  "data": {
    "label": "Sort Data",
    "subtype": "sort",
    "config": {
      "column": "total_amount",
      "direction": "desc",
      "availableColumns": ["category", "total_amount"]
    }
  }
}
```

### 7. Rename Node (Default Type)

**Type**: `"default"`
**Subtype**: `"rename"`

**Config Schema**:
```json
{
  "mappings": [             // Array of column renames
    {
      "old": string,        // Original column name
      "new": string         // New column name
    }
  ],
  "availableColumns": []     // Result columns
}
```

**Example**:
```json
{
  "id": "rename-001",
  "type": "default",
  "position": { "x": 100, "y": 200 },
  "data": {
    "label": "Rename Columns",
    "subtype": "rename",
    "config": {
      "mappings": [
        {"old": "total_amount", "new": "revenue"},
        {"old": "category", "new": "product_category"}
      ],
      "availableColumns": ["product_category", "revenue"]
    }
  }
}
```

### 8. Window Function Node (Default Type)

**Type**: `"default"`
**Subtype**: `"window"`

**Config Schema**:
```json
{
  "partitionBy": string,     // Column to partition by
  "orderBy": string,         // Column to order by
  "alias": string,           // Result column name
  "availableColumns": []     // Result columns
}
```

### 9. Case/When Node (Default Type)

**Type**: `"default"`
**Subtype**: `"case_when"`

**Config Schema**:
```json
{
  "conditions": [
    {
      "when": string,        // Condition expression
      "then": string,        // Value when condition is true
      "column": string,      // Column for simple mode
      "operator": string,    // Operator for simple mode
      "value": string,       // Value for simple mode
      "isAdvanced": boolean  // Whether using advanced mode
    }
  ],
  "elseValue": string,       // Default value
  "alias": string,           // Result column name
  "availableColumns": []     // Result columns
}
```

### 10. Combine Node (Default Type)

**Type**: `"default"`
**Subtype**: `"combine"`

**Config Schema**:
```json
{
  "joinType": string,        // "union" or other join types
  "column": string,          // Column for combining
  "leftColumn": string,      // Left column for joins
  "availableColumns": []     // Result columns
}
```

## Edge Schema

Edges define connections between nodes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | string | Yes | Source node ID |
| `target` | string | Yes | Target node ID |
| `id` | string | Yes | Unique edge identifier |
| `animated` | boolean | No | Whether edge shows animation |
| `style` | object | No | Edge styling (stroke, strokeWidth) |

**Example**:
```json
{
  "source": "input-001",
  "target": "filter-002",
  "id": "xy-edge__input-001-filter-002",
  "animated": true,
  "style": {
    "stroke": "#0052CC",
    "strokeWidth": 2
  }
}
```

## Validation Rules

### 1. Node ID Uniqueness
- All node IDs must be unique within a workflow
- Recommended format: `{type}-{timestamp}`

### 2. Edge References
- All `source` IDs in edges must reference existing nodes
- All `target` IDs in edges must reference existing nodes
- An edge cannot connect a node to itself

### 3. Circular Dependencies
- Workflows must not contain circular dependencies
- A node cannot indirectly reference itself through the edge chain

### 4. Required Fields
- `nodes` array must contain at least one input node
- `edges` array can be empty (for single-node workflows)
- All required fields must be present and non-null

### 5. Position Coordinates
- All nodes must have valid `x` and `y` coordinates
- Coordinates should be positive numbers

### 6. Column References
- All columns referenced in config must exist in `availableColumns`
- `availableColumns` should be updated after each transformation

## Complete Workflow Example

```json
{
  "nodes": [
    {
      "id": "input-001",
      "type": "input",
      "position": { "x": 100, "y": 50 },
      "data": {
        "label": "CSV/Excel File",
        "config": {
          "file": "sales.csv",
          "file_path": "uploads/sales.csv",
          "availableColumns": ["product", "quantity", "price"]
        }
      }
    },
    {
      "id": "filter-002",
      "type": "default",
      "position": { "x": 100, "y": 200 },
      "data": {
        "label": "Filter Records",
        "subtype": "filter",
        "config": {
          "column": "quantity",
          "operator": ">",
          "value": "10",
          "availableColumns": ["product", "quantity", "price"]
        }
      }
    },
    {
      "id": "output-003",
      "type": "output",
      "position": { "x": 100, "y": 350 },
      "data": {
        "label": "Export File",
        "config": {
          "exportFormat": "csv",
          "fileName": "filtered.csv",
          "availableColumns": ["product", "quantity", "price"]
        }
      }
    }
  ],
  "edges": [
    {
      "source": "input-001",
      "target": "filter-002",
      "id": "xy-edge__input-001-filter-002",
      "animated": true
    },
    {
      "source": "filter-002",
      "target": "output-003",
      "id": "xy-edge__filter-002-output-003",
      "animated": true
    }
  ]
}
```

## Reference Workflows

See `/data/workflows/reference/` for complete working examples:
- `input_workflow.json` - Simple input → output
- `filter_workflow.json` - Input → filter → output
- `aggregate_workflow.json` - Input → aggregate → output
- `join_workflow.json` - Two inputs → combine → output
- `sql_workflow.json` - Input → SQL → output
- `multi_node_workflow.json` - Complex 6-node pipeline
