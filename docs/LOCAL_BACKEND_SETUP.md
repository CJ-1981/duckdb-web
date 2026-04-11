# Local Backend + Vercel Frontend Setup Guide

This guide shows you how to run the FastAPI + DuckDB backend locally while hosting the Next.js frontend on Vercel.

## Architecture

```
┌─────────────────────────────────────┐
│   Vercel (Frontend)               │
│   - Next.js 16                    │
│   - Hosted on vercel.app          │
│   - Uses user-configured API URL  │
└──────────────┬──────────────────────┘
               │
               │ User's browser (localhost:8000)
               │
┌──────────────▼──────────────────────┐
│   Local Backend                    │
│   - FastAPI + DuckDB               │
│   - Running on user's machine      │
│   - Port 8000                      │
└─────────────────────────────────────┘
```

## Benefits

✅ **Free Hosting**: Frontend deployed for free on Vercel
✅ **Full Functionality**: All backend features work locally
✅ **Easy Testing**: Test changes without redeploying
✅ **Data Privacy**: Data stays on your local machine
✅ **Development Speed**: Frontend updates deploy automatically

## Setup Instructions

### 1. Backend Configuration

Update your FastAPI CORS configuration in `src/api/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI()

    # Get Vercel deployment URL from environment
    vercel_url = os.getenv("VERCEL_URL", "http://localhost:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",        # Local development
            "http://127.0.0.1:3000",         # Alternative local
            "https://your-app.vercel.app",  # Your Vercel deployment
            vercel_url,                     # Dynamic Vercel URL
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### 2. Environment Variables

Create a `.env` file in your backend directory:

```env
# Vercel deployment URL (update this!)
VERCEL_URL=https://your-app.vercel.app

# OR for development
# VERCEL_URL=http://localhost:3000
```

### 3. Start Local Backend

```bash
# Navigate to your project directory
cd duckdb-web

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Start backend
python -m uvicorn src.api.main:create_app --factory --reload --port 8000
```

### 4. Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
vercel --prod

# Note the deployment URL (e.g., https://your-app.vercel.app)
```

### 5. Configure Frontend

1. Open your deployed Vercel app
2. Click the **Settings** button (gear icon)
3. Enter your local backend URL: `http://localhost:8000`
4. Click **Test & Save**
5. If connection successful, you're ready!

## User Configuration

Users can configure their backend URL in two ways:

### Method 1: Settings Panel (Recommended)

1. Open your deployed app on Vercel
2. Click **Settings** in the toolbar
3. Choose from quick select options:
   - **Local (default)**: `http://localhost:8000`
   - **Local (alternative)**: `http://127.0.0.1:8000`
   - **Network (local IP)**: `http://192.168.1.100:8000`
   - **Production**: Your deployed backend URL
4. Click **Test & Save** to verify connection

### Method 2: Manual URL Entry

1. In Settings panel, enter custom backend URL
2. Examples:
   - `http://localhost:8000` (your local machine)
   - `http://192.168.1.100:8000` (another device on local network)
   - `https://your-backend.railway.app` (cloud backend)

## Common Use Cases

### Development Workflow

1. **Frontend**: Deploy to Vercel for testing
2. **Backend**: Run locally with hot reload
3. **Workflow**: Make backend changes → test immediately on Vercel frontend

### Team Collaboration

1. **Developer**: Runs backend locally
2. **Team**: Accesses frontend on Vercel
3. **Benefit**: No need to deploy backend for every change

### Data Privacy

1. **Sensitive Data**: Never leaves your machine
2. **Processing**: Done entirely locally
3. **Control**: Full control over your data

## Troubleshooting

### Issue: "Connection Failed" Error

**Solutions**:
1. **Check backend is running**: Visit `http://localhost:8000/docs` in your browser
2. **Verify CORS configuration**: Ensure Vercel domain is allowed
3. **Check firewall**: Make sure port 8000 isn't blocked
4. **Try alternative URL**: Use `http://127.0.0.1:8000` instead of `localhost`

### Issue: CORS Errors in Browser Console

**Solution**:
Update backend CORS configuration:
```python
allow_origins=[
    "https://your-app.vercel.app",  # Your exact Vercel URL
    "http://localhost:3000",
]
```

### Issue: Backend Works But Frontend Shows Errors

**Check**:
1. Backend URL is correct (no trailing slashes)
2. Browser console for specific error messages
3. Network tab in DevTools for failed requests

### Issue: Want to Share with Others

**Options**:
1. **Local Network**: Use your local IP address (e.g., `http://192.168.1.100:8000`)
2. **Cloud Backend**: Deploy backend to Railway/Render (~$5/month)
3. **VPN**: Use ngrok or similar for temporary access

## Advanced Configuration

### Multiple Backend Environments

Configure different backends for different purposes:

**Development**:
```bash
# Backend: localhost:8000
# Frontend: localhost:3000
```

**Staging**:
```bash
# Backend: staging-backend.railway.app
# Frontend: staging-app.vercel.app
```

**Production**:
```bash
# Backend: production-backend.railway.app
# Frontend: your-app.vercel.app
```

### Dynamic Backend Switching

Users can switch between backends:
1. Open Settings panel
2. Select different backend URL
3. Click "Test & Save"
4. Frontend automatically uses new backend

### Network Access (LAN)

To access your local backend from other devices on your network:

1. **Find your local IP**:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet "

   # Windows
   ipconfig | findstr "IPv4"
   ```

2. **Update backend binding**:
   ```bash
   # Bind to all interfaces
   python -m uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8000
   ```

3. **Configure frontend**:
   - Use `http://YOUR_LOCAL_IP:8000` in Settings

## Security Considerations

### Local Development

- ✅ Safe: Backend only accessible from your machine
- ⚠️ Caution: Don't expose local backend to internet

### Network Access

- ⚠️ Caution: Anyone on your network can access backend
- ✅ Safe: Use for trusted home/office networks
- ❌ Avoid: Public WiFi networks

### Production Deployment

- ✅ Best: Deploy backend to cloud (Railway/Render)
- ✅ Secure: Use HTTPS and authentication
- ✅ Protected: Configure proper CORS origins

## Performance Tips

### Backend Performance

1. **Use async operations**: Ensure FastAPI endpoints are async
2. **Optimize DuckDB queries**: Use proper indexing and query optimization
3. **Enable caching**: Cache frequently accessed data

### Frontend Performance

1. **Connection timeout**: Set reasonable timeout for backend requests
2. **Error handling**: Graceful fallback when backend unavailable
3. **Loading states**: Show loading indicators during API calls

## Cost Comparison

| Setup | Monthly Cost | Complexity |
|-------|-------------|------------|
| **Vercel Frontend + Local Backend** | Free | Low |
| **Vercel Frontend + Railway Backend** | $5-20 | Medium |
| **Full Cloud (Vercel + Railway)** | $5-40 | High |
| **Self-Hosted Everything** | Server cost | High |

## Next Steps

1. **Test Setup**: Try local backend + Vercel frontend
2. **Configure CORS**: Update backend with Vercel domain
3. **Deploy Frontend**: Push to Vercel
4. **Configure Settings**: Set backend URL in frontend
5. **Test Integration**: Verify full workflow works

## Support

For issues or questions:
- Check browser console for specific errors
- Verify backend is running and accessible
- Review CORS configuration
- Check network connectivity
- See main DEPLOYMENT.md for more details
