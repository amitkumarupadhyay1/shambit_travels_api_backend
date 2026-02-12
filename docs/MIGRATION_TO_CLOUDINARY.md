# Migration Guide: Local Storage to Cloudinary

## Overview
This guide helps you migrate from local file storage to Cloudinary for persistent media storage.

## Why Migrate?

### Current Problem (Local Storage)
- ❌ Files deleted on every deployment (Railway ephemeral storage)
- ❌ No CDN (slow image loading)
- ❌ No automatic optimization
- ❌ Manual backup required

### After Migration (Cloudinary)
- ✅ Files persist forever
- ✅ Global CDN (fast loading worldwide)
- ✅ Automatic optimization (WebP, compression)
- ✅ Free tier: 25GB storage + 25GB bandwidth/month

## Step-by-Step Migration

### Step 1: Get Cloudinary Credentials (5 minutes)

1. Go to https://cloudinary.com
2. Click "Sign Up" (no credit card required)
3. Fill in:
   - Email
   - Password
   - Cloud name (choose wisely, can't change later)
4. Verify email
5. Go to Dashboard
6. Copy credentials:
   ```
   Cloud name: your_cloud_name
   API Key: 123456789012345
   API Secret: abcdefghijklmnopqrstuvwxyz
   ```

### Step 2: Update Environment Variables

**Local Development (.env)**
```bash
# Add to backend/.env
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz
```

**Production (Railway)**
```bash
# Add to Railway environment variables
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz
```

### Step 3: Install Cloudinary Package

```bash
cd backend
pip install cloudinary django-cloudinary-storage
pip freeze > requirements.txt
```

### Step 4: Verify Configuration

```bash
cd backend
python manage.py shell < scripts/verify_cloudinary.py
```

Expected output:
```
============================================================
CLOUDINARY VERIFICATION
============================================================

1. Environment Variables:
   ✅ USE_CLOUDINARY: True
   ✅ CLOUDINARY_CLOUD_NAME: your_cloud_name
   ✅ CLOUDINARY_API_KEY: 1234***
   ✅ CLOUDINARY_API_SECRET: ***

2. Storage Backend:
   Current storage backend: cloudinary_storage.storage.MediaCloudinaryStorage
   ✅ Cloudinary storage is ACTIVE

3. Installed Apps:
   ✅ cloudinary_storage is installed
   ✅ cloudinary is installed

4. Cloudinary Connection:
   ✅ Successfully connected to Cloudinary!
   Status: ok
```

### Step 5: Test Upload

1. Restart Django server:
   ```bash
   python manage.py runserver
   ```

2. Go to Django Admin: http://localhost:8000/admin/

3. Navigate to Media Library → Add Media

4. Upload a test image

5. Check the file URL:
   - ✅ Should start with: `https://res.cloudinary.com/your_cloud_name/`
   - ❌ If starts with `/media/`, Cloudinary is not active

### Step 6: Migrate Existing Files (Optional)

If you have existing files in local storage:

```bash
cd backend
python manage.py migrate_to_cloudinary
```

This script will:
1. Find all media files in local storage
2. Upload them to Cloudinary
3. Update database URLs
4. Keep local files as backup

### Step 7: Deploy to Production

1. Commit changes:
   ```bash
   git add .
   git commit -m "Enable Cloudinary for persistent media storage"
   git push
   ```

2. Railway will automatically deploy

3. Verify in production:
   - Upload a test image via admin
   - Check URL starts with `https://res.cloudinary.com/`
   - Deploy again (push empty commit)
   - Verify image still loads (not 404)

## Verification Checklist

- [ ] Cloudinary account created
- [ ] Credentials added to `.env`
- [ ] `USE_CLOUDINARY=True` set
- [ ] `cloudinary` and `django-cloudinary-storage` installed
- [ ] Verification script passes
- [ ] Test upload shows Cloudinary URL
- [ ] Production environment variables set
- [ ] Production deployment successful
- [ ] Images persist after redeployment

## Troubleshooting

### Issue: "Cloudinary storage is NOT active"

**Solution:**
1. Check `.env` file has correct credentials
2. Ensure `USE_CLOUDINARY=True` (not "true" or "1")
3. Restart Django server
4. Check `backend/backend/settings/storage.py` is loaded

### Issue: "ModuleNotFoundError: No module named 'cloudinary'"

**Solution:**
```bash
pip install cloudinary django-cloudinary-storage
```

### Issue: "Invalid credentials"

**Solution:**
1. Double-check credentials in Cloudinary dashboard
2. Ensure no extra spaces in `.env` file
3. Try regenerating API secret in Cloudinary

### Issue: "Upload works locally but not in production"

**Solution:**
1. Check Railway environment variables are set
2. Verify Railway logs: `railway logs`
3. Check for typos in variable names
4. Ensure Railway has redeployed after adding variables

## Rollback Plan

If something goes wrong:

1. Disable Cloudinary:
   ```bash
   USE_CLOUDINARY=False
   ```

2. Restart server

3. Files will use local storage again

4. Debug the issue before re-enabling

## Cost Monitoring

### Free Tier Limits
- Storage: 25 GB
- Bandwidth: 25 GB/month
- Transformations: 25 credits/month

### Check Usage
```bash
# Via Django command
python manage.py media_stats --cloudinary

# Via Cloudinary Dashboard
https://cloudinary.com/console/usage
```

### Stay Within Free Tier
1. Optimize images before upload (max 2MB)
2. Use `q_auto:low` for quality
3. Delete unused media regularly
4. Use lazy loading on frontend

## Next Steps

After successful migration:

1. ✅ Update frontend to use optimized URLs
2. ✅ Add image loading skeletons
3. ✅ Implement lazy loading
4. ✅ Set up monitoring for usage
5. ✅ Document for team

## Support

**Questions?**
- Cloudinary Docs: https://cloudinary.com/documentation
- Django Integration: https://cloudinary.com/documentation/django_integration

**Issues?**
- Check Django logs: `tail -f logs/django.log`
- Check Railway logs: `railway logs`
- Test locally first before deploying
