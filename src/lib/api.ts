const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export async function executeWorkflow(nodes: any[], edges: any[], previewLimit: number = 50) {
  try {
    const response = await fetch(`${API_BASE_URL}/workflows/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('Backend is unreachable:', error);
    throw error;
  }
}

export async function uploadFile(file: File) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/data/upload`, {
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

export async function saveWorkflow(name: string, nodes: any[], edges: any[]) {
  const response = await fetch(`${API_BASE_URL}/workflows/save?name=${encodeURIComponent(name)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nodes, edges }),
  });
  if (!response.ok) throw new Error("Save failed");
  return await response.json();
}

export async function renameWorkflow(oldName: string, newName: string) {
  const response = await fetch(`${API_BASE_URL}/workflows/rename?old_name=${encodeURIComponent(oldName)}&new_name=${encodeURIComponent(newName)}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Rename failed");
  }
  return await response.json();
}

export async function listSavedWorkflows() {
  const responseArr = await fetch(`${API_BASE_URL}/workflows/list`);
  if (!responseArr.ok) throw new Error("List failed");
  return await responseArr.json();
}

export async function loadWorkflowGraph(name: string) {
  const response = await fetch(`${API_BASE_URL}/workflows/load/${name}`);
  if (!response.ok) throw new Error("Load failed");
  return await response.json();
}

export async function generateReport(nodes: any[], edges: any[], reportConfig: any) {
  try {
    const response = await fetch(`${API_BASE_URL}/workflows/report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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

export async function inspectNode(nodes: any[], edges: any[], nodeId: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/workflows/inspect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

export async function validateSql(sql: string, inputTable?: string, columns?: (string | any)[]) {
  try {
    const payload = {
      sql: sql,
      input_table: inputTable,
      columns: columns
    };

    const response = await fetch(`${API_BASE_URL}/workflows/validate-sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Validation request failed");
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Failed to validate SQL:', error);
    throw error;
  }
}

export async function previewSql(nodes: any[], edges: any[], nodeId: string, sql: string, previewLimit: number = 50) {
  try {
    const response = await fetch(`${API_BASE_URL}/workflows/preview-sql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
