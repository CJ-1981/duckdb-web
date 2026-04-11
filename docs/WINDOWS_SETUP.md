# Windows Setup Guide

## Important: OneDrive and Cloud Storage Warning

**⚠️ Do NOT clone this repository into OneDrive, Dropbox, Google Drive, or any other cloud-synced folder.**

### Why?

Cloud synchronization services cause several issues with development environments:

1. **Virtual Environment Corruption**: Python virtual environments (`.venv`) use symlinks and hardlinks that cloud sync often breaks
2. **node_modules Issues**: npm packages may fail to install or run incorrectly due to file locking
3. **Performance Degradation**: Real-time file sync slows down development tools
4. **Sync Conflicts**: Concurrent file access can create duplicate/conflicted files
5. **Build Failures**: File locking during build processes causes intermittent failures

### Recommended Locations

Clone the repository to a **local** directory:

```
C:\dev\duckdb-web
C:\projects\duckdb-web
D:\code\duckdb-web
%USERPROFILE%\projects\duckdb-web
```

**Avoid**:
```
C:\Users\YourName\OneDrive\Documents\duckdb-web
C:\Users\YourName\Dropbox\projects\duckdb-web
C:\Users\YourName\Google Drive\code\duckdb-web
```

## Installation

### Quick Start

1. **Clone to a safe location** (see above)
2. Run the installer:
   ```cmd
   install.bat
   ```

The installer will:
- Check for Node.js and Python
- Detect if you're in a cloud-synced folder (with warning)
- Create a Python virtual environment
- Install all dependencies

### Custom Virtual Environment Location

If you must work in a cloud-synced folder, create the virtual environment in your user profile:

```cmd
# Create virtual environment in user profile
python -m venv %USERPROFILE%\.venvs\duckdb-web

# Set environment variable to use custom location
set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web

# Activate manually when needed
%USERPROFILE%\.venvs\duckdb-web\Scripts\activate
```

**For permanent configuration**, set the environment variable in System Properties:
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** → **Environment Variables**
3. Add new user variable:
   - Variable name: `VENV_DIR`
   - Variable value: `C:\Users\YourName\.venvs\duckdb-web`

## Running the Application

### Standard Usage

```cmd
run.bat
```

This starts:
- Backend (FastAPI) on http://localhost:8000
- Frontend (Next.js) on http://localhost:3000

### Custom Frontend Port

```cmd
set PORT=4000
run.bat
```

### With Custom Virtual Environment

```cmd
set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web
run.bat
```

## Troubleshooting

### Issue: "Failed to create virtual environment"

**Solution**: You're likely in a OneDrive folder. Move to a local directory.

### Issue: "pip install fails with file locking error"

**Solution**: 
1. Use a custom VENV_DIR (see above)
2. Or disable OneDrive sync temporarily

### Issue: "npm install hangs or fails"

**Solution**:
1. Ensure you're not in a synced folder
2. Try: `npm install --no-bin-links`
3. Or move repository to local directory

### Issue: Backend fails to start

**Solutions**:
1. Check if virtual environment exists: `dir .venv`
2. Try without virtual environment (uses system Python)
3. Ensure port 8000 is not already in use

### Issue: Frontend shows connection errors

**Solutions**:
1. Ensure backend is running (check http://localhost:8000/docs)
2. Check if antivirus/firewall is blocking connections
3. Try different ports: `set PORT=3001 && run.bat`

## Development Tips

### Check Your Current Path

```cmd
echo %CD%
```

Look for these indicators of cloud storage:
- `OneDrive`
- `SkyDrive`
- `Dropbox`
- `Google Drive`
- `iCloudDrive`

### Safe Development Workflow

1. **Always** clone to local directories
2. **Use virtual environments** (default with this project)
3. **Run `install.bat`** after pulling major changes
4. **Check for updates** regularly: `git pull`

### IDE Configuration

**VS Code**:
- Install extensions: Python, ESLint, Prettier
- Set Python interpreter: `.venv\Scripts\python.exe`
- Enable Auto Save

**PyCharm**:
- Open project as existing directory
- Configure Python interpreter: point to `.venv\Scripts\python.exe`
- Enable auto-reload for development

## Performance Optimization

For better performance on Windows:

1. **Exclude from Windows Defender**:
   - Add project directory to exclusions
   - Add `.venv` directory to exclusions
   - Add `node_modules` directory to exclusions

2. **Exclude from Cloud Sync**:
   - Add to OneDrive exclude list
   - Disable real-time sync during development

3. **Use SSD**: If possible, keep project on SSD for faster I/O

## Additional Resources

- [Node.js Installation](https://nodejs.org/)
- [Python Installation](https://www.python.org/downloads/)
- [Git Installation](https://git-scm.com/downloads)
- [Windows Terminal](https://aka.ms/terminal) (recommended for better terminal experience)

## Support

If you encounter issues not covered here:
1. Check the error message carefully
2. Ensure you're not in a cloud-synced folder
3. Try the troubleshooting steps above
4. Check GitHub Issues for similar problems
