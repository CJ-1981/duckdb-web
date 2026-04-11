/**
 * Unified API Client
 * Consolidates all API calls with dynamic backend URL configuration
 * Supports local development backend URL configuration via settings panel
 */

// ─── Backend URL Configuration ────────────────────────────────────────────────

/**
 * Get the configured backend URL
 * Priority: localStorage -> environment variable -> default
 */
export function getBackendUrl(): string {
  // Check if backend URL is configured in window (from settings panel)
  if (typeof window !== 'undefined' && (window as any).BACKEND_URL) {
    return (window as any).BACKEND_URL;
  }

  // Check localStorage
  if (typeof window !== 'undefined') {
    const savedUrl = localStorage.getItem('backend_url');
    if (savedUrl) {
      return savedUrl;
    }
  }

  // Fall back to environment variable
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

/**
 * Set the backend URL (used by settings panel)
 */
export function setBackendUrl(url: string): void {
  if (typeof window !== 'undefined') {
    const cleanUrl = url.replace(/\/$/, '');
    localStorage.setItem('backend_url', cleanUrl);
    (window as any).BACKEND_URL = cleanUrl;
  }
}

/**
 * Reset backend URL to default
 */
export function resetBackendUrl(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('backend_url');
    delete (window as any).BACKEND_URL;
  }
}

// ─── Health & Connection ─────────────────────────────────────────────────────

/**
 * Check if backend is reachable
 */
export async function checkBackendConnection(): Promise<boolean> {
  try {
    const baseUrl = getBackendUrl().replace(/\/$/, '');
    const response = await fetch(`${baseUrl}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Get connection status information
 */
export async function getConnectionInfo(): Promise<{
  connected: boolean;
  backendUrl: string;
  latency?: number;
}> {
  const startTime = Date.now();
  const connected = await checkBackendConnection();
  const latency = connected ? Date.now() - startTime : undefined;

  return {
    connected,
    backendUrl: getBackendUrl(),
    latency,
  };
}

/**
 * Check backend health
 */
export async function checkHealth() {
  try {
    const baseUrl = getBackendUrl().replace(/\/$/, '');
    const response = await fetch(`${baseUrl}/api/health`);
    return await response.json();
  } catch (error) {
    console.error('Backend is unreachable:', error);
    throw error;
  }
}

// ─── API Request Helper ───────────────────────────────────────────────────────

/**
 * Make an API request to the configured backend
 */
async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const baseUrl = getBackendUrl().replace(/\/$/, '');
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

  // Add CORS headers if not present
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  return fetch(url, {
    ...options,
    headers,
  });
}

// ─── Workflow Operations ──────────────────────────────────────────────────────

/**
 * Execute a workflow
 */
export async function executeWorkflow(nodes: any[], edges: any[], previewLimit: number = 50) {
  try {
    const response = await apiRequest('/api/v1/workflows/execute', {
      method: 'POST',
      body: JSON.stringify({ nodes, edges, preview_limit: previewLimit }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to execute workflow:', error);
    throw error;
  }
}

/**
 * Save a workflow
 */
export async function saveWorkflow(name: string, nodes: any[], edges: any[]) {
  const response = await apiRequest(
    `/api/v1/workflows/save?name=${encodeURIComponent(name)}`,
    {
      method: 'POST',
      body: JSON.stringify({ nodes, edges }),
    }
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Save failed');
  }

  return await response.json();
}

/**
 * List all saved workflows
 */
export async function listSavedWorkflows() {
  const response = await apiRequest('/api/v1/workflows/list');

  if (!response.ok) {
    throw new Error('List failed');
  }

  return await response.json();
}

/**
 * Load a workflow by name
 */
export async function loadWorkflowGraph(name: string) {
  const response = await apiRequest(`/api/v1/workflows/load/${encodeURIComponent(name)}`);

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Load failed');
  }

  return await response.json();
}

/**
 * Rename a workflow
 */
export async function renameWorkflow(oldName: string, newName: string) {
  const response = await apiRequest(
    `/api/v1/workflows/rename?old_name=${encodeURIComponent(oldName)}&new_name=${encodeURIComponent(newName)}`,
    {
      method: 'POST',
    }
  );

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Rename failed');
  }

  return await response.json();
}

/**
 * Delete a saved workflow
 */
export async function deleteWorkflow(name: string) {
  const response = await apiRequest(`/api/v1/workflows/delete?name=${encodeURIComponent(name)}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Delete failed');
  }

  return await response.json();
}

// ─── Data Operations ─────────────────────────────────────────────────────────

/**
 * Upload a data file
 */
export async function uploadFile(file: File) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const baseUrl = getBackendUrl().replace(/\/$/, '');
    const response = await fetch(`${baseUrl}/api/v1/data/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to upload file:', error);
    throw error;
  }
}

// ─── Advanced Operations ─────────────────────────────────────────────────────

/**
 * Generate a report from workflow
 */
export async function generateReport(nodes: any[], edges: any[], reportConfig: any) {
  try {
    const response = await apiRequest('/api/v1/workflows/report', {
      method: 'POST',
      body: JSON.stringify({ nodes, edges, report_config: reportConfig }),
    });

    if (!response.ok) {
      throw new Error(`Report generation failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to generate report:', error);
    throw error;
  }
}

/**
 * Inspect a specific node in the workflow
 */
export async function inspectNode(nodes: any[], edges: any[], nodeId: string) {
  try {
    const response = await apiRequest('/api/v1/workflows/inspect', {
      method: 'POST',
      body: JSON.stringify({ nodes, edges, node_id: nodeId }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData?.detail || `Inspection failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to inspect node:', error);
    throw error;
  }
}

/**
 * Validate SQL query
 */
export async function validateSql(sql: string, inputTable?: string, columns?: (string | any)[]) {
  try {
    const payload = {
      sql: sql,
      input_table: inputTable,
      columns: columns
    };

    const response = await apiRequest('/api/v1/workflows/validate-sql', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Validation request failed');
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Failed to validate SQL:', error);
    throw error;
  }
}

/**
 * Preview SQL query results
 */
export async function previewSql(nodes: any[], edges: any[], nodeId: string, sql: string, previewLimit: number = 50) {
  try {
    const response = await apiRequest('/api/v1/workflows/preview-sql', {
      method: 'POST',
      body: JSON.stringify({ nodes, edges, node_id: nodeId, sql, preview_limit: previewLimit }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Preview failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to preview SQL:', error);
    throw error;
  }
}
