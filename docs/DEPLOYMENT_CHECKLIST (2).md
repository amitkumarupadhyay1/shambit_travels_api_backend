# Deployment Checklist - Image Loading Fix

## Pre-Deployment Verification

### Backend
- [x] Python syntax check passed
- [x] CORS headers added to serve_media function
- [x] OPTIONS handler implemented
- [x] Cache-Control headers configured

### Frontend
- [x] ESLint check passed
- [x] Next.js config cleaned up
- [x] Image optimization enabled
- [x] Remote patterns configured

## Deployment Steps

### Step 1: Backend Deployment

```bash
cd backend
git add backend/urls.py
git commit -m "fix: Add CORS headers to media endpoint for Next.js Image Optimization"
git push origin main
```

**Wait for Railway deployment to complete** (~2-3 minutes)

### Step 2: Verify Backend

Test the media endpoint:
```bash
curl -I https://shambit.up.railway.app/media/city_ayodhya_hero.jpg
```

Expected headers:
```
HTTP/2 200
access-control-allow-origin: *
access-control-allow-methods: GET, HEAD, OPTIONS
cache-control: public, max-age=31536000, immutable
content-type: image/jpeg
```

### Step 3: Frontend Deployment

```bash
cd frontend/shambit-frontend
git add next.config.ts test-media-endpoint.js
git commit -m "fix: Configure Next.js for proper image optimization with backend CORS"
git push origin main
```

**Wait for Railway deployment to complete** (~3-5 minutes)

### Step 4: Verify Frontend

1. Open https://shambittravels.up.railway.app
2. Open DevTools (F12)
3. Go to Network tab
4. Filter by "Img"
5. Refresh page
6. Verify images load with 200 status

### Step 5: Test Image Optimization

Check that Next.js is optimizing images:
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

## Post-Deployment Verification

### Browser Tests

1. **Clear Cache**
   - Chrome: Ctrl+Shift+Delete → Clear cached images
   - Firefox: Ctrl+Shift+Delete → Cached Web Content
   - Edge: Ctrl+Shift+Delete → Cached images and files

2. **Test Homepage**
   - Visit: https://shambittravels.up.railway.app
   - Verify: Featured Cities section shows images
   - Check: No 404 errors in console
   - Confirm: Images are responsive

3. **Test Image URLs**
   - Direct: https://shambit.up.railway.app/media/city_ayodhya_hero.jpg
   - Optimized: https://shambittravels.up.railway.app/_next/image?url=...
   - Both should return 200 status

### Performance Tests

1. **Lighthouse Audit**
   - Open DevTools → Lighthouse
   - Run audit on homepage
   - Check "Largest Contentful Paint" score
   - Verify images are optimized

2. **Network Performance**
   - Check image sizes are reduced
   - Verify WebP/AVIF formats are served (if supported)
   - Confirm lazy loading works

### Error Monitoring

Check Railway logs for any errors:

**Backend:**
```bash
railway logs --service shambit-backend
```

**Frontend:**
```bash
railway logs --service shambit-frontend
```

## Rollback Procedure

If issues are detected:

### Backend Rollback
```bash
cd backend
git revert HEAD
git push origin main
```

### Frontend Rollback
```bash
cd frontend/shambit-frontend
git revert HEAD
git push origin main
```

## Success Criteria

- [ ] No 404 errors for image requests
- [ ] Images display correctly on homepage
- [ ] Next.js Image Optimization working
- [ ] CORS headers present in responses
- [ ] No console errors
- [ ] Lighthouse score maintained or improved
- [ ] Page load time not degraded

## Troubleshooting

### Issue: Images still not loading

**Check:**
1. Backend deployment completed successfully
2. Media files exist in backend/media directory
3. CORS headers are present in response
4. Frontend deployment completed successfully

**Solution:**
```bash
# Test backend directly
curl -I https://shambit.up.railway.app/media/city_ayodhya_hero.jpg

# Check Railway logs
railway logs --service shambit-backend
railway logs --service shambit-frontend
```

### Issue: CORS errors in console

**Check:**
1. Backend serve_media function has CORS headers
2. OPTIONS handler is working
3. Access-Control-Allow-Origin is set to '*'

**Solution:**
Verify the backend code matches the fix in IMAGE_LOADING_FIX_SUMMARY.md

### Issue: Images load but are not optimized

**Check:**
1. Next.js config has correct remotePatterns
2. Image component is used (not <img> tag)
3. Image URLs match the remote patterns

**Solution:**
Review next.config.ts and ensure remotePatterns include shambit.up.railway.app

## Contact

If issues persist after following this checklist:
1. Check IMAGE_LOADING_FIX_SUMMARY.md for detailed explanation
2. Review Railway deployment logs
3. Test with test-media-endpoint.js script
4. Verify backend and frontend are both deployed

## Notes

- Both backend and frontend must be deployed for the fix to work
- Clear browser cache after deployment
- Test in incognito mode to avoid cache issues
- Monitor Railway logs during deployment
