# Media Library Testing Guide

## Quick Start Testing

### Prerequisites
1. Backend server running
2. Cloudinary credentials configured in `.env`
3. At least one test media file uploaded

---

## Test 1: Verify Cloudinary Configuration

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if using one)
# Windows: vuuuuenv_cls_repro\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Run Django shell
python manage.py shell
```

```python
# In Django shell, run these commands:
import os
from django.conf import settings

# Check environment variables
print("USE_CLOUDINARY:", os.environ.get("USE_CLOUDINARY"))
print("CLOUD_NAME:", os.environ.get("CLOUDINARY_CLOUD_NAME"))
print("Has API_KEY:", bool(os.environ.get("CLOUDINARY_API_KEY")))
print("Has API_SECRET:", bool(os.environ.get("CLOUDINARY_API_SECRET")))

# Test Cloudinary connection
import cloudinary
import cloudinary.api

try:
    result = cloudinary.api.ping()
    print("\n✅ Cloudinary connection: SUCCESS")
    print("Response:", result)
except Exception as e:
    print("\n❌ Cloudinary connection: FAILED")
    print("Error:", e)

# Exit shell
exit()
```

**Expected Output**:
```
USE_CLOUDINARY: True
CLOUD_NAME: your_cloud_name
Has API_KEY: True
Has API_SECRET: True

✅ Cloudinary connection: SUCCESS
Response: {'status': 'ok'}
```

---

## Test 2: Test Media Deletion via API

### Step 1: Get a test media ID

```bash
# List all media
curl -X GET http://localhost:8000/api/media/ | python -m json.tool
```

Note down a media ID from the response.

### Step 2: Get authentication token

```bash
# Login to get token (replace with your credentials)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your_password"}' \
  | python -m json.tool
```

Copy the `access` token from the response.

### Step 3: Delete the media

```bash
# Replace {MEDIA_ID} and {YOUR_TOKEN}
curl -X DELETE http://localhost:8000/api/media/{MEDIA_ID}/ \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -v
```

**Expected Response**:
```json
{
  "message": "Media deleted successfully",
  "id": 1,
  "file_name": "library/test_image.jpg"
}
```

### Step 4: Check the logs

```bash
# In another terminal, watch the logs
tail -f backend/logs/django.log | grep -i "media\|cloudinary"
```

**Expected Log Messages**:
```
INFO Attempting to delete media id=1 file=library/test_image.jpg public_id=library/test_image
INFO USE_CLOUDINARY=True, public_id=library/test_image
INFO Calling cloudinary.uploader.destroy(public_id=library/test_image, resource_type=image)
INFO Cloudinary deletion result for media id=1: {'result': 'ok'}
INFO Cloudinary deletion successful for media id=1 public_id=library/test_image
```

### Step 5: Verify in Cloudinary Dashboard

1. Go to https://cloudinary.com/console
2. Navigate to Media Library
3. Search for the deleted file
4. Confirm it's no longer there

---

## Test 3: Test Media Update & Cache Busting

### Step 1: Get a media file

```bash
curl -X GET http://localhost:8000/api/media/1/ | python -m json.tool
```

Note the `file_url` and the `?v=timestamp` parameter.

### Step 2: Update the media

```bash
curl -X PATCH http://localhost:8000/api/media/1/ \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "alt_text": "Updated description"}' \
  | python -m json.tool
```

### Step 3: Fetch the media again

```bash
curl -X GET http://localhost:8000/api/media/1/ | python -m json.tool
```

**Verify**:
- `updated_at` timestamp has changed
- `file_url` has a new `?v=timestamp` value
- Title and alt_text are updated

---

## Test 4: Test Frontend Delete Function

### Create a test page

Create `frontend/shambit-frontend/src/app/test-media/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { deleteMedia, getMediaGallery } from '@/lib/media';

export default function TestMediaPage() {
  const [mediaId, setMediaId] = useState('');
  const [token, setToken] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleDelete = async () => {
    const result = await deleteMedia(parseInt(mediaId), token);
    setResult(result);
  };

  const handleListMedia = async () => {
    const gallery = await getMediaGallery(1, 10);
    setResult(gallery);
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Media Library Test</h1>
      
      <div className="space-y-4">
        <div>
          <label className="block mb-2">Media ID:</label>
          <input
            type="number"
            value={mediaId}
            onChange={(e) => setMediaId(e.target.value)}
            className="border p-2 rounded"
          />
        </div>

        <div>
          <label className="block mb-2">JWT Token:</label>
          <input
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="border p-2 rounded w-full"
          />
        </div>

        <div className="space-x-2">
          <button
            onClick={handleDelete}
            className="bg-red-500 text-white px-4 py-2 rounded"
          >
            Delete Media
          </button>

          <button
            onClick={handleListMedia}
            className="bg-blue-500 text-white px-4 py-2 rounded"
          >
            List Media
          </button>
        </div>

        {result && (
          <div className="mt-4 p-4 bg-gray-100 rounded">
            <h2 className="font-bold mb-2">Result:</h2>
            <pre className="overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
```

### Test the page

1. Start frontend: `npm run dev`
2. Navigate to `http://localhost:3000/test-media`
3. Enter a media ID
4. Enter your JWT token
5. Click "Delete Media"
6. Check the result

---

## Test 5: Test File Replacement

### Step 1: Upload a new file to replace existing media

```bash
# Create a test image file first
# Then upload it to replace existing media

curl -X PUT http://localhost:8000/api/media/1/ \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -F "file=@/path/to/new_image.jpg" \
  -F "title=Replaced Image"
```

### Step 2: Check the logs

```bash
tail -f backend/logs/django.log | grep -i "media\|cloudinary"
```

**Expected Log Messages**:
```
INFO Media id=1 file changed from library/old_image.jpg to library/new_image.jpg, deleting old file
INFO Attempting to delete media id=1 file=library/old_image.jpg public_id=library/old_image
INFO Cloudinary deletion successful for media id=1
INFO Media id=1 updated_at will be refreshed
```

---

## Common Issues & Solutions

### Issue: "Cloudinary connection: FAILED"

**Solution**:
1. Check `.env` file has correct credentials
2. Verify `USE_CLOUDINARY=True` (not "true" or "1")
3. Restart Django server after changing `.env`
4. Check Cloudinary dashboard for API credentials

### Issue: "Storage deletion failed"

**Solution**:
1. Check file permissions on media directory
2. Verify MEDIA_ROOT is correctly configured
3. Check if file actually exists

### Issue: "Could not extract public_id"

**Solution**:
1. Check if file URL contains "cloudinary.com"
2. Verify file was uploaded to Cloudinary (not local storage)
3. Check file.name format in database

### Issue: "Frontend delete returns 401 Unauthorized"

**Solution**:
1. Verify JWT token is valid and not expired
2. Check token is passed in Authorization header
3. Ensure user has permission to delete media

### Issue: "Cache not updating after media change"

**Solution**:
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check if `updated_at` timestamp changed
4. Verify `?v=timestamp` parameter in URL is different

---

## Success Indicators

✅ Cloudinary connection test passes
✅ Media deletion removes file from Cloudinary dashboard
✅ Logs show successful deletion messages
✅ Frontend delete function returns success
✅ Media updates change the `?v=timestamp` parameter
✅ File replacement deletes old file from Cloudinary

---

## Monitoring Commands

### Watch logs in real-time
```bash
# All logs
tail -f backend/logs/django.log

# Media-related only
tail -f backend/logs/django.log | grep -i "media"

# Cloudinary-related only
tail -f backend/logs/django.log | grep -i "cloudinary"

# Deletion-related only
tail -f backend/logs/django.log | grep -i "delete"
```

### Check recent errors
```bash
tail -100 backend/logs/django.log | grep -i "error\|exception"
```

### Check Cloudinary usage
```bash
curl -X GET http://localhost:8000/api/media/cloudinary_summary/ | python -m json.tool
```

---

## Performance Testing

### Test bulk deletion
```python
# In Django shell
from media_library.models import Media
from media_library.services.media_service import MediaService

# Get some media IDs
media_ids = list(Media.objects.values_list('id', flat=True)[:5])

# Bulk delete
result = MediaService.bulk_operation(
    media_ids=media_ids,
    action='delete'
)

print(result)
```

### Test concurrent deletions
```bash
# Delete multiple media files simultaneously
for i in {1..5}; do
  curl -X DELETE http://localhost:8000/api/media/$i/ \
    -H "Authorization: Bearer {YOUR_TOKEN}" &
done
wait
```

---

## Cleanup After Testing

```bash
# Remove test page (if created)
rm frontend/shambit-frontend/src/app/test-media/page.tsx

# Clear test logs
> backend/logs/django.log

# Remove test media from Cloudinary dashboard manually
```

