/**
 * API Client Configuration
 * Handles dynamic backend URL configuration for local/production environments
 */

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

/**
 * Make an API request to the configured backend
 */
export async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const baseUrl = getBackendUrl();
  const url = `${baseUrl}${endpoint}`;

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

/**
 * Check if backend is reachable
 */
export async function checkBackendConnection(): Promise<boolean> {
  try {
    const response = await apiRequest('/health', {
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
