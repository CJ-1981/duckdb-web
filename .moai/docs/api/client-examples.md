# API Client Examples

This document provides practical examples for interacting with the DuckDB Web Workflow Builder API using various programming languages and tools.

## Table of Contents
- [Python Examples](#python-examples)
- [JavaScript/Node.js Examples](#javascriptnodejs-examples)
- [cURL Examples](#curl-examples)
- [Postman Collection](#postman-collection)
- [Go Examples](#go-examples)

---

## Python Examples

### Basic Setup

```python
import requests
from datetime import datetime

class WorkflowBuilderClient:
    def __init__(self, base_url="https://api.duckdb-web.com/v1", api_token=None):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, 
            json=data, params=params, timeout=30
        )
        response.raise_for_status()
        return response.json()
```

### Workflow Management

```python
# Create a new workflow
def create_workflow(client, name, description, definition):
    return client._make_request(
        "POST", "/workflows",
        data={
            "name": name,
            "description": description,
            "definition": definition
        }
    )

# Get all workflows
def list_workflows(client, page=1, limit=20, status=None):
    params = {"page": page, "limit": limit}
    if status:
        params["status"] = status
    return client._make_request("GET", "/workflows", params=params)

# Update workflow
def update_workflow(client, workflow_id, name=None, description=None, status=None):
    data = {}
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if status:
        data["status"] = status
    return client._make_request("PUT", f"/workflows/{workflow_id}", data=data)

# Delete workflow
def delete_workflow(client, workflow_id):
    return client._make_request("DELETE", f"/workflows/{workflow_id}")
```

### Job Management

```python
# Create a scheduled job
def create_scheduled_job(client, workflow_id, name, schedule, data=None):
    return client._make_request(
        "POST", "/jobs",
        data={
            "workflowId": workflow_id,
            "name": name,
            "schedule": schedule,
            "data": data or {}
        }
    )

# Execute job immediately
def execute_job(client, job_id):
    return client._make_request("POST", f"/jobs/{job_id}/execute")

# Get job executions
def get_job_executions(client, job_id, limit=20):
    return client._make_request(
        "GET", f"/jobs/{job_id}/executions",
        params={"limit": limit}
    )
```

### Complete Example

```python
# Complete workflow creation and execution
def complete_workflow_example():
    # Initialize client
    client = WorkflowBuilderClient(api_token="your-api-token")
    
    try:
        # Create workflow
        workflow = create_workflow(
            client,
            "Monthly Sales Report",
            "Generate comprehensive sales report",
            {
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
                        "id": "generate_report",
                        "type": "template",
                        "config": {
                            "template": "sales_report.html",
                            "output": "{{report_path}}/sales_report_{{date}}.pdf"
                        }
                    }
                ]
            }
        )
        
        print(f"Created workflow: {workflow['id']}")
        
        # Create scheduled job
        job = create_scheduled_job(
            client,
            workflow_id=workflow['id'],
            name="Monthly Report - November 2023",
            schedule="0 0 1 * *",  # First day of every month
            data={"date_range": {"start": "2023-11-01"}}
        )
        
        print(f"Created job: {job['id']}")
        
        # Execute job immediately (for testing)
        execution_response = execute_job(client, job['id'])
        print(f"Execution started: {execution_response}")
        
        # Monitor execution
        import time
        time.sleep(10)  # Wait for execution to complete
        
        executions = get_job_executions(client, job['id'])
        for execution in executions['executions']:
            print(f"Execution {execution['id']}: {execution['status']}")
            
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
```

---

## JavaScript/Node.js Examples

### Basic Setup

```javascript
const axios = require('axios');

class WorkflowBuilderClient {
    constructor(baseURL = 'https://api.duckdb-web.com/v1', apiToken) {
        this.client = axios.create({
            baseURL,
            headers: {
                'Authorization': `Bearer ${apiToken}`,
                'Content-Type': 'application/json'
            },
            timeout: 30000
        });
        
        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            response => response.data,
            error => {
                if (error.response?.status === 401) {
                    console.error('Authentication failed. Please check your API token.');
                }
                throw error;
            }
        );
    }
}
```

### Workflow Management

```javascript
// Create a new workflow
async function createWorkflow(client, name, description, definition) {
    return await client.client.post('/workflows', {
        name,
        description,
        definition
    });
}

// List workflows with pagination
async function listWorkflows(client, { page = 1, limit = 20, status } = {}) {
    const params = { page, limit };
    if (status) params.status = status;
    
    return await client.client.get('/workflows', { params });
}

// Update workflow
async function updateWorkflow(client, workflowId, updates) {
    return await client.client.put(`/workflows/${workflowId}`, updates);
}

// Delete workflow
async function deleteWorkflow(client, workflowId) {
    return await client.client.delete(`/workflows/${workflowId}`);
}
```

### Job Management

```javascript
// Create scheduled job
async function createScheduledJob(client, workflowId, name, schedule, data = {}) {
    return await client.client.post('/jobs', {
        workflowId,
        name,
        schedule,
        data
    });
}

// Execute job immediately
async function executeJob(client, jobId) {
    return await client.client.post(`/jobs/${jobId}/execute`);
}

// Get job executions
async function getJobExecutions(client, jobId, limit = 20) {
    return await client.client.get(`/jobs/${jobId}/executions`, {
        params: { limit }
    });
}

// Monitor job execution
async function monitorJobExecution(client, jobId, callback) {
    const checkExecution = async () => {
        const executions = await getJobExecutions(client, jobId);
        const latestExecution = executions.executions[0];
        
        if (latestExecution) {
            callback(latestExecution);
            
            // Stop monitoring if execution is completed
            if (['completed', 'failed', 'cancelled'].includes(latestExecution.status)) {
                return false;
            }
        }
        
        return true; // Continue monitoring
    };
    
    // Poll every 5 seconds
    const poll = async () => {
        const shouldContinue = await checkExecution();
        if (shouldContinue) {
            setTimeout(poll, 5000);
        }
    };
    
    poll();
}
```

### Complete Example

```javascript
// Complete workflow example with async/await
async function completeWorkflowExample() {
    const client = new WorkflowBuilderClient('https://api.duckdb-web.com/v1', 'your-api-token');
    
    try {
        // Create workflow
        const workflow = await createWorkflow(client, 
            'Monthly Sales Report',
            'Generate comprehensive sales report',
            {
                steps: [
                    {
                        id: 'extract_data',
                        type: 'database',
                        config: {
                            query: 'SELECT * FROM sales WHERE date >= ?',
                            params: ['{{date_range.start}}']
                        }
                    },
                    {
                        id: 'generate_report',
                        type: 'template',
                        config: {
                            template: 'sales_report.html',
                            output: '{{report_path}}/sales_report_{{date}}.pdf'
                        }
                    }
                ]
            }
        );
        
        console.log(`Created workflow: ${workflow.id}`);
        
        // Create scheduled job
        const job = await createScheduledJob(client,
            workflowId: workflow.id,
            name: 'Monthly Report - November 2023',
            schedule: '0 0 1 * *', // First day of every month
            data: { date_range: { start: '2023-11-01' } }
        );
        
        console.log(`Created job: ${job.id}`);
        
        // Execute job immediately
        const executionResponse = await executeJob(client, job.id);
        console.log(`Execution started:`, executionResponse);
        
        // Monitor execution
        monitorJobExecution(client, job.id, (execution) => {
            console.log(`Execution status: ${execution.status}`);
            if (execution.error_message) {
                console.log(`Error: ${execution.error_message}`);
            }
        });
        
    } catch (error) {
        console.error('Error:', error.message);
        if (error.response) {
            console.error('Response:', error.response.data);
        }
    }
}
```

---

## cURL Examples

### Authentication Setup

```bash
# Set up environment variables
export BASE_URL="https://api.duckdb-web.com/v1"
export API_TOKEN="your-api-token-here"

# Common headers
HEADERS="-H 'Authorization: Bearer $API_TOKEN' -H 'Content-Type: application/json'"
```

### Workflow Operations

```bash
# Create workflow
curl -X POST "$BASE_URL/workflows" \
  $HEADERS \
  -d '{
    "name": "Monthly Sales Report",
    "description": "Generate comprehensive sales report",
    "definition": {
      "steps": [
        {
          "id": "extract_data",
          "type": "database",
          "config": {
            "query": "SELECT * FROM sales WHERE date >= ?",
            "params": ["{{date_range.start}}"]
          }
        }
      ]
    }
  }'

# List workflows
curl -X GET "$BASE_URL/workflows?page=1&limit=10&status=active" \
  $HEADERS

# Get specific workflow
curl -X GET "$BASE_URL/workflows/550e8400-e29b-41d4-a716-446655440000" \
  $HEADERS

# Update workflow
curl -X PUT "$BASE_URL/workflows/550e8400-e29b-41d4-a716-446655440000" \
  $HEADERS \
  -d '{
    "name": "Updated Sales Report",
    "status": "inactive"
  }'

# Delete workflow
curl -X DELETE "$BASE_URL/workflows/550e8400-e29b-41d4-a716-446655440000" \
  $HEADERS
```

### Job Operations

```bash
# Create scheduled job
curl -X POST "$BASE_URL/jobs" \
  $HEADERS \
  -d '{
    "workflowId": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Monthly Report - November 2023",
    "schedule": "0 0 1 * *",
    "data": {
      "date_range": {
        "start": "2023-11-01"
      }
    }
  }'

# List jobs
curl -X GET "$BASE_URL/jobs?status=pending&limit=5" \
  $HEADERS

# Execute job immediately
curl -X POST "$BASE_URL/jobs/550e8400-e29b-41d4-a716-446655440002/execute" \
  $HEADERS

# Cancel job
curl -X PUT "$BASE_URL/jobs/550e8400-e29b-41d4-a716-446655440002/cancel" \
  $HEADERS

# Get job executions
curl -X GET "$BASE_URL/jobs/550e8400-e29b-41d4-a716-446655440002/executions?limit=10" \
  $HEADERS
```

### Monitoring

```bash
# Get system metrics
curl -X GET "$BASE_URL/metrics" \
  $HEADERS

# Get workflow with pagination
curl -X GET "$BASE_URL/workflows?page=2&limit=50" \
  $HEADERS

# Search workflows
curl -X GET "$BASE_URL/workflows?search=sales" \
  $HEADERS
```

---

## Postman Collection

### Setting Up Postman

1. Create a new collection named "DuckDB Workflow Builder API"
2. Add environment variables:
   - `base_url`: `https://api.duckdb-web.com/v1`
   - `api_token`: `your-api-token`

### Request Templates

#### 1. Create Workflow
```http
POST {{base_url}}/workflows

Authorization: Bearer {{api_token}}
Content-Type: application/json

{
    "name": "Monthly Sales Report",
    "description": "Generate comprehensive sales report",
    "definition": {
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
                "id": "generate_report",
                "type": "template",
                "config": {
                    "template": "sales_report.html",
                    "output": "{{report_path}}/sales_report_{{date}}.pdf"
                }
            }
        ]
    }
}
```

#### 2. List Workflows
```http
GET {{base_url}}/workflows?page=1&limit=10&status=active

Authorization: Bearer {{api_token}}
```

#### 3. Create Job
```http
POST {{base_url}}/jobs

Authorization: Bearer {{api_token}}
Content-Type: application/json

{
    "workflowId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Monthly Report - November 2023",
    "schedule": "0 0 1 * *",
    "data": {
        "date_range": {
            "start": "2023-11-01"
        }
    }
}
```

#### 4. Execute Job
```http
POST {{base_url}}/jobs/{{job_id}}/execute

Authorization: Bearer {{api_token}}
```

---

## Go Examples

### Basic Client Setup

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type WorkflowBuilderClient struct {
    baseURL    string
    apiToken   string
    httpClient *http.Client
}

func NewWorkflowBuilderClient(baseURL, apiToken string) *WorkflowBuilderClient {
    return &WorkflowBuilderClient{
        baseURL:    baseURL,
        apiToken:   apiToken,
        httpClient: &http.Client{Timeout: 30 * time.Second},
    }
}

func (c *WorkflowBuilderClient) doRequest(method, endpoint string, data interface{}) (*http.Response, error) {
    url := c.baseURL + endpoint
    
    var body io.Reader
    if data != nil {
        jsonData, err := json.Marshal(data)
        if err != nil {
            return nil, err
        }
        body = bytes.NewBuffer(jsonData)
    }
    
    req, err := http.NewRequest(method, url, body)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Authorization", "Bearer "+c.apiToken)
    req.Header.Set("Content-Type", "application/json")
    
    return c.httpClient.Do(req)
}
```

### Workflow Management

```go
// Create workflow
func (c *WorkflowBuilderClient) CreateWorkflow(name, description string, definition interface{}) (map[string]interface{}, error) {
    data := map[string]interface{}{
        "name":        name,
        "description": description,
        "definition":  definition,
    }
    
    resp, err := c.doRequest("POST", "/workflows", data)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}

// List workflows
func (c *WorkflowBuilderClient) ListWorkflows(page, limit int, status string) (map[string]interface{}, error) {
    params := fmt.Sprintf("?page=%d&limit=%d", page, limit)
    if status != "" {
        params += "&status=" + status
    }
    
    resp, err := c.doRequest("GET", "/workflows"+params, nil)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}

// Execute job
func (c *WorkflowBuilderClient) ExecuteJob(jobID string) (map[string]interface{}, error) {
    resp, err := c.doRequest("POST", "/jobs/"+jobID+"/execute", nil)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}
```

### Complete Example

```go
func main() {
    client := NewWorkflowBuilderClient(
        "https://api.duckdb-web.com/v1",
        "your-api-token",
    )
    
    // Create workflow
    definition := map[string]interface{}{
        "steps": []map[string]interface{}{
            {
                "id":   "extract_data",
                "type": "database",
                "config": map[string]interface{}{
                    "query":  "SELECT * FROM sales WHERE date >= ?",
                    "params": []string{"{{date_range.start}}"},
                },
            },
        },
    }
    
    workflow, err := client.CreateWorkflow(
        "Monthly Sales Report",
        "Generate comprehensive sales report",
        definition,
    )
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Created workflow: %v\n", workflow["id"])
    
    // Create job
    jobData := map[string]interface{}{
        "workflowId": workflow["id"],
        "name":      "Monthly Report - November 2023",
        "schedule":  "0 0 1 * *",
        "data": map[string]interface{}{
            "date_range": map[string]interface{}{
                "start": "2023-11-01",
            },
        },
    }
    
    job, err := client.CreateJobFromData(jobData)
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Created job: %v\n", job["id"])
    
    // Execute job
    execution, err := client.ExecuteJob(job["id"].(string))
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Execution started: %v\n", execution)
}
```

## Error Handling Examples

### Python Error Handling

```python
def safe_api_request(client, endpoint, method="GET", data=None):
    try:
        response = client._make_request(method, endpoint, data)
        return response, None
    except requests.exceptions.HTTPError as e:
        error_details = {
            'status_code': e.response.status_code,
            'error_data': e.response.json(),
            'endpoint': endpoint
        }
        return None, error_details
    except requests.exceptions.RequestException as e:
        error_details = {
            'error': str(e),
            'endpoint': endpoint
        }
        return None, error_details
```

### JavaScript Error Handling

```javascript
class APIError extends Error {
    constructor(message, status, details) {
        super(message);
        this.status = status;
        this.details = details;
    }
}

async function safeAPIRequest(client, endpoint, method = 'GET', data = null) {
    try {
        const response = await client.client.request({
            method,
            url: endpoint,
            data
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            throw new APIError(
                error.response.data.message || 'API Error',
                error.response.status,
                error.response.data
            );
        }
        throw new APIError('Network Error', 0, { error: error.message });
    }
}
```