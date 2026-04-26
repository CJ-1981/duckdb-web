# Getting Started with DuckDB Web Workflow Builder

Welcome to the DuckDB Web Workflow Builder! This guide will help you get up and running with our workflow automation system quickly and easily.

## Prerequisites

Before you begin, make sure you have:

- **DuckDB Web Account**: Sign up at [duckdb-web.com](https://duckdb-web.com)
- **Browser**: Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)
- **API Access**: API key for programmatic access (optional)

## First Steps

### 1. Sign In and Navigate to Dashboard

1. Visit [duckdb-web.com](https://duckdb-web.com) and sign in
2. Click on "Workflows" in the main navigation
3. You'll land on the **Workflow Dashboard**

### 2. Understanding the Interface

The main interface consists of:

- **Navigation Bar**: Switch between Workflows, Jobs, Monitor, and Settings
- **Content Area**: Main workspace showing workflows, jobs, or monitoring data
- **Action Buttons**: Primary actions like "Create Workflow", "Run Job", etc.
- **Status Indicators**: Real-time status information

![Dashboard Interface](../../assets/dashboard-interface.png)

*Note: Dashboard screenshot shows main navigation and workspace areas*

### 3. Your First Workflow

#### Step 1: Create a New Workflow

1. Click **"Create Workflow"** in the top-right corner
2. Fill in the basic information:
   - **Name**: "My First Workflow" (descriptive name)
   - **Description**: Brief description of what the workflow does
   - **Status**: "Active" (can change later)

#### Step 2: Add Workflow Steps

A workflow is a series of steps that execute in sequence. Let's create a simple data processing workflow:

```json
{
  "name": "Sales Data Processing",
  "description": "Extract sales data and generate monthly report",
  "steps": [
    {
      "id": "extract_data",
      "type": "database",
      "config": {
        "query": "SELECT * FROM sales WHERE date >= ?",
        "params": ["{{date_range.start}}"]
      }
    },
    {
      "id": "transform_data",
      "type": "python",
      "config": {
        "script": "transform_sales_data.py",
        "params": {
          "input_data": "{{extract_data.output}}"
        }
      }
    },
    {
      "id": "generate_report",
      "type": "template",
      "config": {
        "template": "sales_report.html",
        "output": "{{report_path}}/sales_report_{{date}}.pdf"
      }
    }
  ]
}
```

#### Step 3: Save and Configure

1. Click **"Save Workflow"**
2. Your workflow is now saved and ready to use
3. You'll be redirected to the workflow details page

### 4. Understanding Workflow Concepts

#### Types of Workflow Steps

| Step Type | Description | Common Use Cases |
|-----------|-------------|------------------|
| **Database** | Execute SQL queries | Data extraction, updates, deletes |
| **Python** | Run Python scripts | Data transformation, complex calculations |
| **Template** | Generate files from templates | Reports, documents, exports |
| **Email** | Send emails | Notifications, reports, alerts |
| **HTTP** | Make web requests | API calls, web scraping |
| **File** | Handle file operations | Upload, download, process files |

#### Step Parameters

Steps can use parameters for flexibility:

- **Static values**: Fixed strings, numbers, or booleans
- **Dynamic values**: References from previous steps using `{{step_id.output}}`
- **System variables**: `{{date}}`, `{{time}}`, `{{user_id}}`
- **Environment variables**: Values from your environment configuration

### 5. Creating Your First Job

A job is an instance of a workflow with specific parameters and schedule.

#### Manual Job Creation

1. Go to your workflow details page
2. Click **"Create Job"**
3. Configure job parameters:
   - **Name**: Descriptive name for this specific job
   - **Schedule**: When to run (see Job Scheduling section)
   - **Data**: Input parameters for the workflow

#### Example Job Configuration

```json
{
  "name": "Monthly Sales Report - November 2023",
  "schedule": "0 0 1 * *",  // First day of each month at midnight
  "data": {
    "date_range": {
      "start": "2023-11-01",
      "end": "2023-11-30"
    },
    "report_path": "/reports/sales"
  }
}
```

### 6. Testing Your Workflow

Before scheduling a job, it's important to test your workflow:

1. **Quick Test**: Run the workflow with test data
2. **Validation**: Check that all steps execute correctly
3. **Debugging**: Use the built-in debugger to troubleshoot issues

#### How to Test

1. On your workflow page, click **"Test"**
2. Enter test data for each step
3. Click **"Run Test"**
4. Review the results and logs

### 7. Monitoring and Troubleshooting

#### Job Monitoring

Once you have jobs running, you can monitor them:

1. Go to the **Monitor** tab
2. View active, completed, and failed jobs
3. Click on any job to see detailed execution information

#### Understanding Job Status

| Status | Description | Action Required |
|--------|-------------|----------------|
| **Pending** | Job is scheduled and waiting | None |
| **Running** | Job is currently executing | Monitor progress |
| **Completed** | Job finished successfully | Review results |
| **Failed** | Job encountered errors | Investigate and retry |
| **Cancelled** | Job was cancelled manually | None |

#### Viewing Logs

For detailed debugging, you can view execution logs:

1. Click on a job execution
2. Navigate to the **Logs** tab
3. View step-by-step execution details
4. Download logs for offline analysis

### 8. Common Issues and Solutions

#### Problem: Workflow Fails to Execute

**Symptoms**: Job status shows "Failed" with no clear error message

**Solutions**:
1. Check the **Logs** tab for detailed error information
2. Verify database connectivity and credentials
3. Ensure all required files and templates exist
4. Test individual steps separately

#### Problem: Job Not Running on Schedule

**Symptoms**: Jobs show "Pending" but never execute

**Solutions**:
1. Check the schedule format (cron expression)
2. Verify the service has proper permissions
3. Check system time and timezone settings
4. Review job execution history for patterns

#### Problem: Performance Issues

**Symptoms**: Jobs run slowly or time out

**Solutions**:
1. Optimize database queries
2. Increase timeout settings for long-running operations
3. Break large workflows into smaller steps
4. Monitor system resources

### 9. Best Practices

#### Workflow Design

- **Keep it simple**: Break complex processes into smaller workflows
- **Use meaningful names**: Name steps and jobs clearly
- **Add documentation**: Include descriptions and comments in complex workflows
- **Version control**: Create versions of workflows before making major changes

#### Job Management

- **Schedule strategically**: Avoid peak hours for resource-intensive jobs
- **Monitor regularly**: Check job status and logs periodically
- **Have fallback plans**: Implement retry logic for critical jobs
- **Clean up old jobs**: Archive or delete completed jobs to maintain performance

### 10. Next Steps

Now that you have your first workflow running, you might want to explore:

- **Advanced Features**: Check out the [Advanced Features Guide](advanced-features.md)
- **Job Scheduling**: Learn about scheduling jobs in the [Job Scheduling Guide](job-scheduling.md)
- **API Access**: Integrate with your applications using the [API Documentation](../api/)
- **Troubleshooting**: Get help with specific issues in the [Troubleshooting Guide](monitoring-troubleshooting.md)

### Support and Resources

- **Documentation**: Full documentation available at [docs.duckdb-web.com](https://docs.duckdb-web.com)
- **Community**: Join our community forum at [community.duckdb-web.com](https://community.duckdb-web.com)
- **Support**: Contact support@duckdb-web.com for assistance

---

*Happy workflow automation! 🚀*