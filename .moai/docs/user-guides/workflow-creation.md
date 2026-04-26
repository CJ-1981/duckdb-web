# Workflow Creation and Management

This guide covers everything you need to know about creating and managing workflows in the DuckDB Web Workflow Builder system.

## Table of Contents
- [Understanding Workflows](#understanding-workflows)
- [Creating a New Workflow](#creating-a-new-workflow)
- [Workflow Steps and Components](#workflow-steps-and-components)
- [Managing Workflow Versions](#managing-workflow-versions)
- [Workflow Best Practices](#workflow-best-practices)
- [Advanced Workflow Features](#advanced-features)

---

## Understanding Workflows

A workflow is a sequence of automated steps that execute in order to accomplish a specific task. Workflows are the building blocks of your automation system.

### Key Concepts

- **Workflow Definition**: The blueprint that describes what steps to execute
- **Workflow Version**: A snapshot of a workflow definition at a specific point in time
- **Active Version**: The version currently being used for new jobs
- **Job**: An execution instance of a workflow with specific parameters

### Workflow Lifecycle

```
Create → Configure → Test → Deploy → Monitor → Update → Archive
```

---

## Creating a New Workflow

### Basic Workflow Creation

1. Navigate to the **Workflows** tab
2. Click **"Create Workflow"**
3. Fill in the workflow details:
   - **Name**: A descriptive name (max 100 characters)
   - **Description**: Brief explanation of what the workflow does
   - **Initial Status**: Choose between "Active", "Draft", or "Inactive"

### Workflow Definition Editor

The workflow definition uses JSON format to define the steps and their configurations.

#### Basic Workflow Structure

```json
{
  "name": "Monthly Sales Report",
  "description": "Generate comprehensive monthly sales report",
  "steps": [
    {
      "id": "step_id",
      "type": "step_type",
      "config": {
        // Configuration parameters
      },
      "retry": {
        "max_attempts": 3,
        "delay": 5000
      }
    }
  ],
  "variables": {
    // Global variables accessible to all steps
  }
}
```

### Step Types and Their Configurations

#### 1. Database Steps

Execute SQL queries against your DuckDB database.

```json
{
  "id": "extract_sales_data",
  "type": "database",
  "config": {
    "query": "SELECT * FROM sales WHERE date BETWEEN ? AND ?",
    "params": ["{{date_range.start}}", "{{date_range.end}}"],
    "connection": "primary_db",
    "output_format": "table"
  }
}
```

**Parameters:**
- `query`: SQL query to execute
- `params`: Query parameters (use `{{variable}}` syntax for dynamic values)
- `connection`: Database connection name
- `output_format`: How to format results (table, json, csv)

#### 2. Python Steps

Execute Python scripts for data processing and transformations.

```json
{
  "id": "transform_data",
  "type": "python",
  "config": {
    "script": "transform_sales_data.py",
    "python_version": "3.9",
    "params": {
      "input_data": "{{extract_sales_data.output}}",
      "output_path": "{{output_directory}}/transformed.csv"
    },
    "env_vars": {
      "PYTHONPATH": "/custom/path"
    }
  }
}
```

**Parameters:**
- `script`: Python script filename
- `python_version`: Python interpreter version
- `params`: Input parameters and file paths
- `env_vars`: Environment variables

#### 3. Template Steps

Generate files from templates.

```json
{
  "id": "generate_report",
  "type": "template",
  "config": {
    "template": "sales_report.html",
    "data": {
      "sales_data": "{{transform_data.output}}",
      "date": "{{date_range.end}}",
      "total_sales": "{{calculate_total_sales.result}}"
    },
    "output": "{{output_directory}}/sales_report_{{date}}.pdf"
  }
}
```

**Parameters:**
- `template`: Template filename
- `data`: Data to inject into template
- `output`: Output file path with variables

#### 4. Email Steps

Send email notifications.

```json
{
  "id": "send_notification",
  "type": "email",
  "config": {
    "to": ["manager@company.com", "team@company.com"],
    "subject": "Sales Report for {{date_range.end}}",
    "body": "The monthly sales report is ready for review.",
    "attachments": ["{{output_directory}}/sales_report_{{date}}.pdf"],
    "connection": "smtp_server"
  }
}
```

**Parameters:**
- `to`: Recipient email addresses
- `subject`: Email subject with variables
- `body`: Email body content
- `attachments`: File attachments
- `connection`: SMTP connection name

#### 5. HTTP Steps

Make web requests to external APIs.

```json
{
  "id": "call_webhook",
  "type": "http",
  "config": {
    "method": "POST",
    "url": "https://api.example.com/webhook",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{api_token}}"
    },
    "body": {
      "data": "{{transform_data.output}}",
      "timestamp": "{{timestamp}}"
    },
    "timeout": 30000
  }
}
```

**Parameters:**
- `method`: HTTP method (GET, POST, PUT, DELETE)
- `url`: Target URL with variables
- `headers`: HTTP headers
- `body`: Request body
- `timeout`: Request timeout in milliseconds

#### 6. File Steps

Handle file operations.

```json
{
  "id": "upload_file",
  "type": "file",
  "config": {
    "action": "upload",
    "source": "{{output_directory}}/sales_report_{{date}}.pdf",
    "destination": "s3://reports-bucket/monthly/",
    "credentials": "aws_credentials",
    "metadata": {
      "author": "workflow_system",
      "category": "sales"
    }
  }
}
```

**Parameters:**
- `action`: File operation (upload, download, copy, delete)
- `source`: Source file path
- `destination`: Target location
- `credentials`: Credential profile name
- `metadata`: File metadata

---

## Managing Workflow Versions

### Creating New Versions

When you need to update a workflow, it's best to create a new version:

1. Navigate to the workflow details page
2. Click **"Create New Version"**
3. Update the workflow definition
4. Save the new version

### Version Management

- **Current Version**: The version used for new jobs
- **Version History**: View all previous versions
- **Rollback**: Switch back to a previous version if needed

#### Version Control Example

```json
{
  "version": "2.1.0",
  "previous_version": "2.0.0",
  "changes": [
    {
      "type": "enhancement",
      "description": "Added data validation step",
      "step_id": "validate_input"
    }
  ]
}
```

### Best Practices for Versioning

1. **Semantic Versioning**: Use version numbers like 1.0.0, 1.1.0, 2.0.0
2. **Document Changes**: Include change notes with each version
3. **Test Before Deploy**: Always test new versions in a non-production environment
4. **Maintain Compatibility**: Consider backward compatibility when making changes

---

## Workflow Variables and Parameters

### Global Variables

Define variables that are accessible across all steps:

```json
{
  "variables": {
    "date_range": {
      "start": "2023-01-01",
      "end": "2023-01-31"
    },
    "output_directory": "/tmp/workflow_output",
    "api_token": "{{secrets.api_token}}"
  }
}
```

### Step Parameters

Use variables within step configurations:

```json
{
  "id": "extract_data",
  "type": "database",
  "config": {
    "query": "SELECT * FROM sales WHERE date >= ?",
    "params": ["{{variables.date_range.start}}"]
  }
}
```

### Variable Types

| Type | Description | Example |
|------|-------------|---------|
| **String** | Text values | `"Hello World"` |
| **Number** | Numeric values | `42`, `3.14` |
| **Boolean** | True/false values | `true`, `false` |
| **Array** | List of values | `[1, 2, 3]` |
| **Object** | Key-value pairs | `{"key": "value"}` |
| **Secret** | Secure values from secrets store | `{{secrets.api_token}}` |

---

## Error Handling and Retry Logic

### Retry Configuration

Add retry logic to handle transient failures:

```json
{
  "id": "unreliable_step",
  "type": "database",
  "config": {
    "query": "SELECT * FROM external_system"
  },
  "retry": {
    "max_attempts": 3,
    "delay": 5000,
    "backoff_multiplier": 2,
    "conditions": [
      "connection_error",
      "timeout"
    ]
  }
}
```

### Error Handling Strategies

| Strategy | Use Case | Example |
|----------|----------|---------|
| **Retry** | Transient network issues | Database connection failures |
| **Skip** | Non-critical failures | Optional notification emails |
| **Fail Fast** | Critical failures | Invalid input data |
| **Fallback** | Alternative processing | Use backup data source |

### Conditional Execution

Use conditions to control workflow flow:

```json
{
  "id": "conditional_step",
  "type": "python",
  "config": {
    "script": "process_data.py",
    "condition": "{{previous_step.output.count}} > 0"
  },
  "skip_on_failure": false
}
```

---

## Advanced Workflow Features

### Parallel Execution

Run multiple steps in parallel to improve performance:

```json
{
  "parallel_steps": [
    {
      "id": "extract_sales",
      "type": "database",
      "config": {
        "query": "SELECT * FROM sales"
      }
    },
    {
      "id": "extract_products",
      "type": "database",
      "config": {
        "query": "SELECT * FROM products"
      }
    }
  ],
  "next_step": {
    "id": "merge_data",
    "type": "python",
    "config": {
      "script": "merge_data.py",
      "params": {
        "sales": "{{parallel_steps.extract_sales.output}}",
        "products": "{{parallel_steps.extract_products.output}}"
      }
    }
  }
}
```

### Loop Structures

Repeat steps for processing multiple items:

```json
{
  "id": "process_items",
  "type": "loop",
  "config": {
    "items": "{{get_items.output}}",
    "steps": [
      {
        "id": "process_item",
        "type": "python",
        "config": {
          "script": "process_single_item.py",
          "params": {
            "item": "{{item}}"
          }
        }
      }
    ]
  }
}
```

### Workflow Dependencies

Define dependencies between workflows:

```json
{
  "id": "child_workflow",
  "type": "workflow",
  "config": {
    "workflow_id": "550e8400-e29b-41d4-a716-446655440001",
    "params": {
      "parent_data": "{{parent_step.output}}"
    },
    "wait_for_completion": true
  }
}
```

---

## Workflow Testing and Validation

### Built-in Testing Tools

1. **Step-by-Step Testing**: Test each step individually
2. **End-to-End Testing**: Test the complete workflow
3. **Mock Data Testing**: Use test data without affecting production

### Testing Workflow Example

```json
{
  "name": "Test Sales Report Workflow",
  "description": "Test workflow with sample data",
  "test_data": {
    "date_range": {
      "start": "2023-01-01",
      "end": "2023-01-31"
    }
  },
  "expected_outputs": {
    "generate_report": {
      "file_exists": true,
      "file_size_min": 1000
    }
  }
}
```

### Debug Mode

Enable debug mode for detailed logging:

```json
{
  "debug": {
    "enabled": true,
    "level": "debug",
    "output_to_console": true,
    "save_logs": true
  }
}
```

---

## Monitoring and Performance

### Real-time Monitoring

Monitor workflow execution in real-time:
- **Live logs** for each step
- **Progress indicators** showing completion percentage
- **Resource usage** tracking

### Performance Metrics

Track key performance indicators:
- **Execution time** for each step
- **Memory usage** during execution
- **Database query performance**
- **Network latency** for external calls

### Optimization Tips

1. **Step Order**: Place resource-intensive steps later in the workflow
2. **Parallel Processing**: Use parallel steps for independent operations
3. **Batch Operations**: Process multiple items in single steps when possible
4. **Caching**: Cache results of expensive operations

---

## Security Considerations

### Input Validation

Validate all inputs to prevent injection attacks:

```json
{
  "id": "validate_input",
  "type": "python",
  "config": {
    "script": "validate_input.py",
    "validation_rules": {
      "date_format": "YYYY-MM-DD",
      "numeric_fields": ["amount", "quantity"],
      "required_fields": ["customer_id", "product_id"]
    }
  }
}
```

### Secure Configuration

- **Use secrets** for sensitive data like API tokens
- **Limit permissions** for each step type
- **Audit logs** for security events
- **Network segmentation** for external connections

---

## Common Workflow Patterns

### 1. Data ETL Pipeline

```json
{
  "name": "ETL Pipeline",
  "steps": [
    {"id": "extract", "type": "database", "config": {...}},
    {"id": "transform", "type": "python", "config": {...}},
    {"id": "validate", "type": "python", "config": {...}},
    {"id": "load", "type": "database", "config": {...}}
  ]
}
```

### 2. Report Generation

```json
{
  "name": "Monthly Reports",
  "steps": [
    {"id": "collect_data", "type": "database", "config": {...}},
    {"id": "calculate_metrics", "type": "python", "config": {...}},
    {"id": "generate_pdf", "type": "template", "config": {...}},
    {"id": "send_email", "type": "email", "config": {...}}
  ]
}
```

### 3. Monitoring and Alerting

```json
{
  "name": "System Monitoring",
  "steps": [
    {"id": "check_metrics", "type": "http", "config": {...}},
    {"id": "analyze_thresholds", "type": "python", "config": {...}},
    {"id": "create_alert", "type": "email", "config": {...}},
    {"id": "log_event", "type": "database", "config": {...}}
  ]
}
```

---

## Troubleshooting Common Issues

### Issue: Workflow Fails to Start

**Possible Causes:**
- Invalid workflow definition syntax
- Missing required configuration
- Permission issues

**Solutions:**
1. Validate JSON syntax
2. Check configuration parameters
3. Verify user permissions

### Issue: Step Fails Mid-Execution

**Possible Causes:**
- Resource limits exceeded
- External service unavailable
- Invalid input data

**Solutions:**
1. Check step logs for error details
2. Increase resource limits if needed
3. Implement proper error handling

### Issue: Performance Issues

**Possible Causes:**
- Large data sets
- Network latency
- Inefficient queries

**Solutions:**
1. Optimize database queries
2. Implement pagination
3. Use caching where appropriate

---

## Next Steps

Now that you understand workflow creation and management, you might want to explore:

- **Job Scheduling**: [Job Scheduling Guide](job-scheduling.md)
- **Monitoring**: [Monitoring and Troubleshooting](monitoring-troubleshooting.md)
- **API Integration**: [API Documentation](../api/)
- **Advanced Features**: [Advanced Features Guide](advanced-features.md)

### Resources

- **Documentation**: [Full documentation](https://docs.duckdb-web.com)
- **Community**: [Community forum](https://community.duckdb-web.com)
- **Support**: [Contact support](mailto:support@duckdb-web.com)