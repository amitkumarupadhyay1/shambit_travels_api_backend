# Media Library Fixes - Quick Reference

## 🎯 What Was Fixed

1. ✅ Cloudinary deletion now works properly
2. ✅ Media updates reflect on frontend (cache-busting)
3. ✅ Frontend has delete/update/upload functions

---

## 📁 Files Changed

### Backend
- `backend/apps/media_library/views.py`
- `backend/apps/media_library/services/media_service.py`
- `backend/apps/media_library/signals.py`

### Frontend
- `frontend/shambit-frontend/src/lib/media.ts`

---

## 🔧 Quick Test

### Test Cloudinary Connection
```bash
cd backend
python manage.py shell
```
```python
import os
print("USE_CLOUDINARY:", os.environ.get("USE_CLOUDINARY"))

import cloudinary.api
print("Connection:", cloudinary.api.ping())
exit()
```

### Test Deletion
```bash
# Get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# Delete media (replace {ID} and {TOKEN})
curl -X DELETE http://localhost:8000/api/media/{ID}/ \
  -H "Authorization: Bearer {TOKEN}"
```

### Check Logs
```bash
tail -f backend/logs/django.log | grep -i "media\|cloudinary"
```

---

## 💻 Frontend Usage

```typescript
import { deleteMedia, updateMedia, uploadMedia } from '@/lib/media';

// Delete
const result = await deleteMedia(mediaId, token);
if (result.success) {
  console.log('Deleted!');
}

// Update
const updated = await updateMedia(mediaId, {
  title: 'New Title',
  alt_text: 'New description'
}, token);

// Upload
const newMedia = await uploadMedia(file, {
  title: 'My Image',
  content_type: 'cities.city',
  object_id: 1
}, token);
```

---

## 🔍 Expected Log Output

```
INFO Attempting to delete media id=1 file=library/test.jpg public_id=library/test
INFO USE_CLOUDINARY=True, public_id=library/test
INFO Calling cloudinary.uploader.destroy(...)
INFO Cloudinary deletion result: {'result': 'ok'}
INFO Cloudinary deletion successful for media id=1
```

---

## ⚙️ Environment Variables

```bash
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

---

## 📚 Documentation

- `MEDIA_LIBRARY_ANALYSIS.md` - Problem analysis
- `MEDIA_FIXES_IMPLEMENTED.md` - Detailed implementation
- `MEDIA_TESTING_GUIDE.md` - Testing instructions
- `MEDIA_FIXES_SUMMARY.md` - Executive summary
- `IMPLEMENTATION_COMPLETE.md` - Deployment guide
- `QUICK_REFERENCE.md` - This file

---

## 🚨 Troubleshooting

**Deletion fails?**
- Check Cloudinary credentials
- Verify `USE_CLOUDINARY=True`
- Check logs for errors

**Updates not showing?**
- Hard refresh browser (Ctrl+Shift+R)
- Check `?v=timestamp` in URL changed
- Verify `updated_at` timestamp updated

**Frontend 401 error?**
- Token expired - get new token
- Check Authorization header format
- Verify user permissions

---

## ✅ Success Indicators

- ✅ Logs show "Cloudinary deletion successful"
- ✅ File removed from Cloudinary dashboard
- ✅ Database record deleted
- ✅ No errors in logs
- ✅ Frontend functions return success

---

## 🚀 Deploy

```bash
# Backend
git add backend/apps/media_library/
git commit -m "fix: enhance media deletion with Cloudinary support"
git push

# Frontend
git add frontend/shambit-frontend/src/lib/media.ts
git commit -m "feat: add media CRUD operations"
git push
```

---

## 📞 Need Help?

1. Check logs: `tail -f backend/logs/django.log`
2. Test connection: See "Quick Test" above
3. Review: `MEDIA_TESTING_GUIDE.md`
4. Verify: Environment variables set correctly

