# Windows Setup Guide for DuckDB Web

This guide covers Windows-specific setup instructions and common issues.

## Prerequisites

### Required Software

1. **Node.js 22 LTS** or later
   - Download: https://nodejs.org/
   - Choose "LTS" version
   - Install with default options
   - Verify: `node --version` (should show v22.x.x)

2. **Python 3.12** or later
   - Download: https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation
   - Verify: `python --version` (should show 3.12.x)

3. **Git** (for version control)
   - Download: https://git-scm.com/download/win
   - Install with default options

### Optional but Recommended

4. **Visual Studio Build Tools** (for native Python packages)
   - Download: https://visualstudio.microsoft.com/downloads/
   - Install "Build Tools for Visual Studio"
   - Select "C++ build tools"

## Quick Start

### 1. Open Terminal

- **PowerShell** (recommended) or Command Prompt
- Right-click Start → Windows PowerShell → "Open as Administrator"
- Navigate to project: `cd C:\path\to\duckdb-web`

### 2. Install Dependencies

```powershell
# Install frontend dependencies
npm install

# (Optional) Create Python virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### 3. Run Development Server

```batch
# Windows users can use the batch script
run.bat

# Or use npm scripts
npm run dev
```

## Windows-Specific Considerations

### 🚫 Avoid Cloud-Synced Directories

**Do NOT** run this project from:
- OneDrive
- Dropbox
- Google Drive
- iCloud Drive
- SharePoint

**Why?** Cloud sync can cause:
- Virtual environment corruption
- File locking issues
- Dependency installation failures
- Hot-reload not working

**Recommended locations:**
- `C:\dev\duckdb-web`
- `C:\projects\duckdb-web`
- `%USERPROFILE%\projects\duckdb-web`

### 🔧 PowerShell Execution Policy

If you see "running scripts is disabled" errors:

```powershell
# Check current policy
Get-ExecutionPolicy

# Allow scripts for current user (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or allow all scripts (not recommended)
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process
```

### 🌐 Network/Firewall Issues

If `npm install` fails:

1. **Check antivirus/firewall** - Temporarily disable if needed
2. **Use npm mirror** (if in China/restricted regions):
   ```powershell
   npm config set registry https://registry.npmmirror.com
   ```
3. **Corporate proxy** - Configure npm proxy:
   ```powershell
   npm config set proxy http://proxy.example.com:8080
   npm config set https-proxy http://proxy.example.com:8080
   ```

### 🐍 Python Virtual Environment Issues

If `.venv\Scripts\Activate.ps1` fails:

```powershell
# Check execution policy
Get-ExecutionPolicy -List

# Allow virtual environment scripts
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Alternative: Use batch file instead
.venv\Scripts\activate.bat
```

## Troubleshooting

### Problem: "Module not found" errors

**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules
Remove-Item -Recurse -Force node_modules

# Reinstall
npm install
```

### Problem: Port already in use (3000, 8000)

**Solution:**
```powershell
# Find process using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>

# Or use a different port
npm run dev:3001
```

### Problem: Python not found after installation

**Solution:**
```powershell
# Check if Python is in PATH
python --version

# If not found, add to PATH manually:
# 1. Search "Environment Variables" in Windows Start
# 2. Click "Edit the system environment variables"
# 3. Click "Environment Variables"
# 4. Add to PATH: C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312
# 5. Add Scripts: C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python312\Scripts
```

### Problem: Long path names on Windows

**Solution:**
```powershell
# Enable long path support (Windows 10+)
# Run as Administrator in PowerShell:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

## Development Scripts

### Available npm Scripts

```bash
# Development
npm run dev              # Start dev server on port 3000
npm run dev:3001         # Start dev server on port 3001
npm run dev:windows      # Windows-specific dev command

# Building
npm run build            # Build for production
npm run start            # Start production server

# Testing
npm run test             # Run E2E tests
npm run test:e2e         # Run Playwright E2E tests
npm run test:e2e:ui      # Run E2E tests with UI
npm run test:unit        # Run unit tests (if configured)

# Linting
npm run lint             # Run ESLint
npm run typecheck        # Run TypeScript type checking
```

### Using the Batch Script

The `run.bat` script automatically:
- ✅ Checks for cloud-synced directories
- ✅ Kills orphaned processes from previous runs
- ✅ Validates environment variables
- ✅ Cleans up on exit (Ctrl+C)

```batch
# Run with default port (3000)
run.bat

# Run with custom port
set PORT=3001
run.bat
```

## Performance Tips

### 1. Use Windows Terminal

Download from Microsoft Store for better performance and features:
- Tabbed interface
- Better Unicode support
- Copy/paste improvements

### 2. Exclude node_modules from Windows Defender

Add to Windows Defender exclusions:
- Project directory
- `node_modules` folder
- `.npm` cache directory

### 3. Use SSD

If possible, keep project on SSD (not HDD) for:
- Faster `npm install`
- Faster hot reload
- Better build performance

## Getting Help

### Common Error Messages

| Error | Solution |
|-------|----------|
| `'python' is not recognized` | Install Python and add to PATH |
| `'npm' is not recognized` | Install Node.js and restart terminal |
| `EPERM: operation not permitted` | Run as Administrator |
| `ENOSPC: no space left` | Clear disk space or disable npm cache |
| `EACCES: permission denied` | Run as Administrator or check file permissions |

### Check Your Environment

```powershell
# Check all versions
node --version
npm --version
python --version
git --version

# Check environment variables
echo $env:PATH
echo $env:PYTHONPATH
echo $env:PORT

# Check running processes
tasklist | findstr /i "node python"
```

### Reset Everything

If nothing works:

```powershell
# 1. Close all terminals and IDEs
# 2. Run as Administrator
Remove-Item -Recurse -Force node_modules, .next, dist
npm cache clean --force
npm install
```

## Additional Resources

- [Node.js Windows Guide](https://nodejs.org/en/docs/guides/anatomy-of-a-nodejs-app-on-windows/)
- [Python Windows Installation](https://docs.python.org/3/using/windows.html)
- [PowerShell Basics](https://docs.microsoft.com/en-us/powershell/scripting/learn/ps101/01-getting-started)
