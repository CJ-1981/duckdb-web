# Development Scripts

This directory contains utility scripts for development.

## dev.js

Smart development server startup script that automatically finds an available port.

### Usage

```bash
npm run dev
# or
node scripts/dev.js
```

### Behavior

The script tries ports in sequence:
1. **Port 3000** (default)
2. **Port 3001** (if 3000 is busy)
3. **Port 3002** (if 3001 is busy)
4. **Port 3003** (if 3002 is busy)

If all ports are in use, the script exits with an error.

### Output Example

```
🚀 Starting Next.js dev server...

🔍 Checking port 3000...
❌ Port 3000 is in use
🔍 Checking port 3001...
❌ Port 3001 is in use
🔍 Checking port 3002...
✅ Port 3002 is available!

🎯 Starting on port 3002...

ready - started server on 0.0.0.0:3002, url: http://localhost:3002
```

### Why This Script?

During development, you might have multiple services running (backend, frontend, E2E tests). This script eliminates the need to:
- Manually check which ports are free
- Edit scripts to change ports
- Remember which port you're using

Just run `npm run dev` and it handles the rest! 🎯
