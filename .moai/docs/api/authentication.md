# Authentication & Authorization

## Overview

The DuckDB Web Workflow Builder API uses JWT (JSON Web Token) authentication for securing all endpoints. This document explains how authentication works and how to properly authenticate your API requests.

## Authentication Flow

### 1. Obtain API Credentials

API credentials are provided to users through the DuckDB Web Workflow Builder interface:

1. Navigate to **Settings > API Keys**
2. Click **"Generate New API Key"**
3. Copy the API key immediately (you won't be able to see it again)

### 2. JWT Token Structure

Each JWT token contains the following claims:

```json
{
  "sub": "user@example.com",
  "iss": "duckdb-web",
  "exp": 1735689600,
  "iat": 1707116800,
  "roles": ["workflow_manager"],
  "permissions": [
    "workflows:read",
    "workflows:write",
    "jobs:read",
    "jobs:write",
    "executions:read"
  ]
}
```

### 3. Token Lifecycle

- **Expiration**: Tokens expire after 24 hours
- **Renewal**: Generate a new token before expiration
- **Revocation**: Tokens can be revoked through the API Keys interface

## Authorization

### Role-Based Access Control (RBAC)

The system uses roles to determine what actions users can perform:

| Role | Description | Permissions |
|------|-------------|-------------|
| **Viewer** | Can only view workflows and jobs | workflows:read, jobs:read, executions:read |
| **Editor** | Can create and edit workflows and jobs | workflows:read, workflows:write, jobs:read, jobs:write, executions:read |
| **Admin** | Full system access including user management | All permissions |

### Permission Matrix

| Resource | Read | Write | Delete | Schedule |
|----------|------|-------|--------|----------|
| **Workflows** | ✅ | ✅ | ✅ | ❌ |
| **Jobs** | ✅ | ✅ | ❌ | ✅ |
| **Executions** | ✅ | ❌ | ❌ | ❌ |

## API Usage

### Making Authenticated Requests

All API requests must include the JWT token in the Authorization header:

```bash
curl -X GET "https://api.duckdb-web.com/v1/workflows" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Common Authentication Errors

| Error Code | Description | Solution |
|------------|-------------|---------|
| `401 Unauthorized` | Missing or invalid token | Generate a new API key |
| `403 Forbidden` | Insufficient permissions | Contact administrator for role upgrade |
| `429 Too Many Requests` | Rate limit exceeded | Implement rate limiting in client |

## Best Practices

### 1. Token Storage
- Store tokens securely (never in source code)
- Use environment variables for development
- Implement secure storage mechanisms in production

### 2. Token Refresh
- Implement automatic token refresh before expiration
- Store refresh logic in client-side applications

### 3. Security Considerations
- Never expose tokens in client-side code (unless using proper OAuth flows)
- Use HTTPS for all API communications
- Implement CORS policies in client applications

### 4. Rate Limiting
- Max 100 requests per minute per API key
- Burst rate of 20 requests per second
- Include `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers in responses

## Example: Complete Authentication Workflow

```python
import requests
import time

class WorkflowBuilderClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.duckdb-web.com/v1"
        self.token = None
        self.token_expiry = 0
        
    def get_token(self):
        # Get JWT token using API key
        response = requests.post(
            f"{self.base_url}/auth/token",
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        self.token = response.json()["token"]
        self.token_expiry = time.time() + 86400  # 24 hours
        return self.token
        
    def _ensure_authenticated(self):
        if not self.token or time.time() > self.token_expiry - 60:
            self.get_token()
            
    def list_workflows(self):
        self._ensure_authenticated()
        response = requests.get(
            f"{self.base_url}/workflows",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()
```

## API Client Libraries

### JavaScript (Node.js)
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://api.duckdb-web.com/v1',
  headers: {
    'Authorization': `Bearer ${process.env.DUCKDB_API_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Set up response interceptor for automatic token refresh
client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Refresh token logic here
    }
    return Promise.reject(error);
  }
);
```

### Python
```python
import requests
from requests.auth import AuthBase

class JWTAuth(AuthBase):
    def __init__(self, token):
        self.token = token
        
    def __call__(self, request):
        request.headers['Authorization'] = f'Bearer {self.token}'
        return request

client = requests.Session()
client.auth = JWTAuth('your-jwt-token')
```

## Troubleshooting

### Common Issues

1. **Invalid Token Errors**
   - Check token expiration
   - Verify token format (no extra whitespace)
   - Generate new token if corrupted

2. **Permission Denied Errors**
   - Verify user role in the system
   - Check required permissions for specific operations

3. **Rate Limit Issues**
   - Implement exponential backoff for retry logic
   - Consider implementing request queuing

### Debugging Tips

- Use the `X-Request-ID` header for tracking requests
- Check `X-Trace-ID` in error responses for debugging
- Log authentication events for security auditing

## Security Headers

The API includes several security headers in all responses:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

These headers help protect against common web security vulnerabilities.