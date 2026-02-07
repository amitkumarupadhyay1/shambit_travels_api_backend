# Quick Deployment Guide - Image Loading Fix

## TL;DR

Images are broken because backend is missing CORS headers. This fix adds them.

## Quick Deploy (Copy & Paste)

### 1. Deploy Backend

```bash
cd backend
git add backend/urls.py
git commit -m "fix: Add CORS headers to media endpoint for Next.js Image Optimization"
git push origin main
```

Wait 2-3 minutes for Railway deployment.

### 2. Deploy Frontend

```bash
cd frontend/shambit-frontend
git add next.config.ts test-media-endpoint.js test-city-images.js
git commit -m "fix: Configure Next.js for proper image optimization with backend CORS"
git push origin main
```

Wait 3-5 minutes for Railway deployment.

### 3. Test

```bash
cd frontend/shambit-frontend
node test-media-endpoint.js
```

Expected output:
```
✅ Image endpoint is working!
✅ CORS headers are present
✅ Content-Type is correct
✅ CORS preflight is working correctly!
```

### 4. Verify in Browser

1. Open: https://shambittravels.up.railway.app
2. Press F12 (DevTools)
3. Check Console - should see no errors
4. Check Network tab - images should load with 200 status

## What Changed?

### Backend (backend/backend/urls.py)
- Added CORS headers to media endpoint
- Added OPTIONS handler for preflight requests

### Frontend (frontend/shambit-frontend/next.config.ts)
- Cleaned up image configuration
- Kept remote patterns for backend URLs

## If Something Goes Wrong

### Rollback Backend
```bash
cd backend
git revert HEAD
git push origin main
```

### Rollback Frontend
```bash
cd frontend/shambit-frontend
git revert HEAD
git push origin main
```

## Need More Details?

- **Full explanation:** See `IMAGE_LOADING_FIX_SUMMARY.md`
- **Step-by-step guide:** See `DEPLOYMENT_CHECKLIST.md`
- **Technical details:** See `IMAGE_LOADING_FLOW.md`
- **All changes:** See `IMAGE_FIX_CHANGES.md`

## Quick Test Commands

```bash
# Test backend media endpoint
curl -I https://shambit.up.railway.app/media/city_ayodhya_hero.jpg

# Test frontend
cd frontend/shambit-frontend
node test-media-endpoint.js
node test-city-images.js

# Check Railway logs
railway logs --service shambit-backend
railway logs --service shambit-frontend
```

## Success Checklist

- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Test script shows ✅ for all checks
- [ ] Homepage loads without errors
- [ ] Images display correctly
- [ ] No 404 errors in console

## Done!

After both deployments complete and tests pass, images should load correctly on the production site.
