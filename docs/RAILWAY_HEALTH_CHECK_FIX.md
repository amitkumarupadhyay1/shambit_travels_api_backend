# Railway Health Check Fix

## Issue
Railway health checks were failing with the error:
```
Invalid HTTP_HOST header: 'healthcheck.railway.app'. You may need to add 'healthcheck.railway.app' to ALLOWED_HOSTS.
```

## Solution Applied

### 1. Updated Production Settings
Modified `backend/settings/production.py` to automatically include Railway health check domains:

```python
# Railway specific settings
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Add Railway health check and internal domains
ALLOWED_HOSTS.extend([
    "healthcheck.railway.app",
    "*.railway.app", 
    "*.up.railway.app",
])
```

### 2. Updated Environment Variables
Updated `.env.railway` to include the health check domain:
```
ALLOWED_HOSTS=shambit.up.railway.app,*.railway.app,healthcheck.railway.app,localhost,127.0.0.1
```

### 3. Health Check Configuration
The health check is properly configured in:
- **Endpoint**: `/health/` (defined in `backend/urls.py`)
- **Railway Config**: `railway.json` specifies `healthcheckPath: "/health/"`
- **Timeout**: 300 seconds (5 minutes)

## Deployment Steps

1. **Push the changes** to your repository
2. **Railway will automatically redeploy** with the updated settings
3. **Health checks should now pass** within a few minutes

## Verification

After deployment, you can verify the health check works by:

```bash
# Test the health endpoint directly
curl https://your-app.up.railway.app/health/

# Expected response:
{
  "status": "healthy",
  "service": "shambit-travels-api", 
  "version": "1.0.0",
  "database": "connected"
}
```

## Additional Notes

- The health check endpoint tests database connectivity
- Railway's internal health checker uses the domain `healthcheck.railway.app`
- The fix ensures this domain is always allowed, regardless of environment variables
- No changes needed to Railway environment variables - the fix is automatic

## Files Modified

1. `backend/settings/production.py` - Added Railway health check domains
2. `.env.railway` - Updated ALLOWED_HOSTS example
3. `test_health_check.py` - Added local testing script (optional)