# Deployment Guide

## Current Architecture

This is a **full-stack application** with:
- **Frontend**: Next.js 16.2.1 (React 19)
- **Backend**: FastAPI (Python 3.12+)
- **Database**: DuckDB (embedded)
- **Features**: CSV upload, data processing, workflow canvas, AI query building

## Deployment Options

### Option 1: Full-Stack Deployment (Recommended) ✅

**Best for**: Production use with full functionality

**Architecture**: Separate hosting for frontend and backend

#### Frontend Deployment (Vercel)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Deploy Frontend**:
   ```bash
   vercel --prod
   ```

3. **Configure Environment Variables**:
   - In Vercel Dashboard → Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend-url.com`

#### Backend Deployment Options

**Option A: Railway** (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy backend
railway login
railway init
railway up
```

**Option B: Render**
```bash
# Install Render CLI
npm install -g render-cli

# Deploy backend
render deploy
```

**Option C: Fly.io**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy backend
fly launch
fly deploy
```

#### Configuration Files

Create `requirements.txt` for backend dependencies:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
duckdb==1.0.0
pandas==2.2.0
reportlab==4.2.0
tabulate==0.9.0
pydantic==2.9.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.0
```

Create `Dockerfile` for container deployment:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 2: Vercel Serverless (Complex) 🔧

**Best for**: Single-platform deployment

**Requirements**: Major refactoring of backend

**Steps**:
1. Convert FastAPI endpoints to Vercel serverless functions
2. Replace DuckDB with serverless-compatible database (Neon, Supabase)
3. Implement serverless file storage (Vercel Blob, AWS S3)
4. Handle cold starts and execution time limits

**Estimated Effort**: 2-3 days of development

### Option 3: Frontend-Only Deployment (Limited) ⚠️

**Best for**: Testing frontend UI only

**Deploy to Vercel**:
```bash
vercel --prod
```

**Limitations**:
- No backend functionality
- No data processing
- No file uploads
- Static pages only

## Environment Configuration

### Frontend Environment Variables

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Feature Flags
NEXT_PUBLIC_ENABLE_AUTH=true
NEXT_PUBLIC_ENABLE_WORKFLOWS=true
```

### Backend Environment Variables

```env
# Database
DATABASE_URL=sqlite:///./duckdb_data.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
FRONTEND_URL=https://your-frontend.vercel.app

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=/tmp/uploads
```

## Deployment Checklist

### Pre-Deployment

- [ ] Update API URL in frontend configuration
- [ ] Set up production database (if needed)
- [ ] Configure CORS for production domains
- [ ] Set environment variables
- [ ] Test API connectivity
- [ ] Optimize assets and bundle size

### Post-Deployment

- [ ] Verify frontend deployment
- [ ] Test backend health endpoints
- [ ] Check API integration
- [ ] Test file upload functionality
- [ ] Monitor error logs
- [ ] Set up monitoring and analytics

## Platform-Specific Instructions

### Vercel Deployment

1. **Connect Repository**:
   - Import GitHub repository to Vercel
   - Configure build settings

2. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

### Railway Deployment

1. **Create New Project**:
   ```bash
   railway init
   ```

2. **Configure**:
   - Set Python version to 3.12
   - Add environment variables
   - Configure port 8000

3. **Deploy**:
   ```bash
   railway up
   ```

### Render Deployment

1. **Create Web Service**:
   - Connect GitHub repository
   - Select Python environment
   - Set build command and start command

2. **Configure**:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn src.api.main:create_app --factory --host 0.0.0.0 --port 8000`

3. **Deploy**:
   - Automatic deployment on git push

## Performance Optimization

### Frontend Optimization

```javascript
// next.config.js
module.exports = {
  compress: true,
  swcMinify: true,
  images: {
    domains: ['your-backend.com'],
  },
  output: 'standalone', // For better deployment
}
```

### Backend Optimization

```python
# Use connection pooling
# Implement caching
# Optimize DuckDB queries
# Use async operations
```

## Monitoring and Logging

### Recommended Tools

- **Frontend**: Vercel Analytics, Sentry
- **Backend**: Sentry, LogRocket, Datadog
- **Uptime**: UptimeRobot, Pingdom

## Troubleshooting

### Common Issues

**CORS Errors**:
```python
# Update backend CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**API Connection Issues**:
- Verify NEXT_PUBLIC_API_URL is set correctly
- Check backend health endpoint
- Review CORS configuration

**File Upload Issues**:
- Verify file size limits
- Check storage permissions
- Review multipart form configuration

## Cost Estimates

### Monthly Costs (Approximate)

**Frontend (Vercel)**:
- Hobby: Free
- Pro: $20/month

**Backend (Railway)**:
- Starter: $5/month
- Professional: $20/month

**Database/Storage**:
- Vercel Blob: Free tier available
- AWS S3: ~$1-5/month

**Total**: $5-40/month depending on usage

## Security Considerations

1. **Environment Variables**: Never commit secrets
2. **API Authentication**: Implement proper JWT/auth
3. **File Upload**: Validate and sanitize uploads
4. **CORS**: Configure strict origins
5. **Rate Limiting**: Implement API rate limits
6. **HTTPS**: Force HTTPS in production

## Support

For deployment issues:
- Check platform documentation
- Review error logs
- Test locally with production configuration
- Use platform community support
