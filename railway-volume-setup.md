# Railway Volume Setup for Media Files

## Problem
Railway containers are ephemeral - they get recreated on each deployment, losing uploaded files.

## Solution: Railway Volume

### 1. Create a Volume in Railway
1. Go to your Railway backend project
2. Click on "Variables" tab
3. Click "New Variable" 
4. Add: `RAILWAY_VOLUME_MOUNT_PATH=/app/media-volume`
5. Go to "Settings" tab
6. Scroll down to "Volumes"
7. Click "Add Volume"
8. Set:
   - **Mount Path**: `/app/media-volume`
   - **Size**: 1GB (or as needed)

### 2. Redeploy
After adding the volume, Railway will redeploy your app with persistent storage.

### 3. Re-upload Images
You'll need to re-upload your images through Django admin since the old ones were lost.

## Alternative: Cloud Storage

For production apps, consider using:
- **AWS S3** - Most popular, reliable
- **Cloudinary** - Image optimization included
- **Google Cloud Storage** - Good integration with other Google services

The `storage.py` file is already configured for these options.

## Current Status
- ✅ Media serving is configured in production
- ✅ Volume support is added to settings
- ⏳ Need to create Railway volume
- ⏳ Need to re-upload images after volume is created