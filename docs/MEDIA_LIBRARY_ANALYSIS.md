# Media Library Issues Analysis & Fix Plan

## Date: 2026-02-14
## Status: Investigation Complete - Ready for Implementation

---

## Issues Identified

### 1. Cloudinary Deletion Not Working ✅ FOUND
**Location**: `backend/apps/media_library/services/media_service.py`

**Problem**: The `delete_media_file()` method exists and attempts Cloudinary deletion, BUT it's only called from signals. The ViewSet's `destroy()` method is NOT overridden, so it uses the default DRF behavior which only deletes the database record.

**Current Flow**:
```
DELETE /api/media/{id}/ 
  → ModelViewSet.destroy() (default DRF)
  → media.delete() (Django ORM)
  → pre_delete signal fires
  → delete_media_file_on_delete() signal handler
  → MediaService.delete_media_file()
```

**Issue**: The signal-based approach SHOULD work, but there may be:
- Signal not properly connected
- Cloudinary credentials not configured
- Error being silently caught

### 2. Media Updates Not Reflecting on Frontend ✅ FOUND
**Location**: Multiple files

**Problem**: Cache invalidation exists in signals, but:
- Frontend uses `cache: 'no-store'` which should bypass cache
- The issue is likely the cache-busting query parameter in URLs
- When media is updated, the `updated_at` timestamp changes, which should update the `?v=timestamp` parameter
- BUT if the frontend is caching the media list response, it won't fetch the new URL

**Current Cache Busting**:
```typescript
// In serializers.py
def _append_cache_buster(self, url: str, obj) -> str:
    timestamp = int(updated_at.timestamp())
    query_params["v"] = str(timestamp)
```

**Issue**: The cache buster works, but:
- Frontend might be caching the API response itself
- Browser might be caching the image despite the query parameter
- The `updated_at` field might not be updating when file changes

### 3. Missing Frontend Delete Functionality ✅ FOUND
**Location**: `frontend/shambit-frontend/src/lib/media.ts`

**Problem**: No delete function exists in the frontend media library. The backend supports DELETE, but frontend has no way to call it.

---

## Root Cause Analysis

### Issue #1: Cloudinary Deletion
The code structure is correct, but we need to verify:
1. Is `USE_CLOUDINARY` environment variable set to "True"?
2. Are Cloudinary credentials properly configured?
3. Is the signal properly registered?
4. Are errors being logged?

### Issue #2: Frontend Cache
The problem is multi-layered:
1. API response caching (even with `cache: 'no-store'`)
2. Browser image caching
3. CDN caching (if Cloudinary CDN is used)
4. The `updated_at` field only updates on `.save()`, not on file replacement

### Issue #3: Missing Delete Function
Simple - just not implemented in frontend.

---

## Fix Plan

### Fix #1: Ensure Cloudinary Deletion Works

**Step 1**: Add explicit logging to track deletion
**Step 2**: Override the `destroy()` method in ViewSet for explicit control
**Step 3**: Add error handling and response feedback
**Step 4**: Verify signal registration

### Fix #2: Fix Cache Invalidation

**Step 1**: Ensure `updated_at` is updated when file changes
**Step 2**: Add stronger cache-busting headers
**Step 3**: Add Cloudinary invalidation on update
**Step 4**: Update frontend to force refresh after updates

### Fix #3: Add Frontend Delete Function

**Step 1**: Add `deleteMedia()` function to `media.ts`
**Step 2**: Add proper authentication headers
**Step 3**: Add error handling

---

## Implementation Priority

1. **HIGH**: Fix Cloudinary deletion (Issue #1)
2. **HIGH**: Add frontend delete function (Issue #3)
3. **MEDIUM**: Fix cache invalidation (Issue #2)

---

## Files to Modify

### Backend
1. `backend/apps/media_library/views.py` - Override destroy() method
2. `backend/apps/media_library/services/media_service.py` - Enhance logging
3. `backend/apps/media_library/signals.py` - Verify signal registration
4. `backend/apps/media_library/serializers.py` - Add cache headers

### Frontend
1. `frontend/shambit-frontend/src/lib/media.ts` - Add delete function
2. Any admin components that manage media - Add delete UI

---

## Testing Plan

### Test #1: Cloudinary Deletion
1. Upload a test image
2. Verify it appears in Cloudinary dashboard
3. Delete via API
4. Verify it's removed from Cloudinary
5. Check logs for any errors

### Test #2: Cache Invalidation
1. Upload an image
2. Update the image (replace file)
3. Verify frontend shows new image immediately
4. Check browser network tab for cache headers

### Test #3: Frontend Delete
1. Call delete function from frontend
2. Verify media is deleted from database
3. Verify media is deleted from Cloudinary
4. Verify UI updates correctly

---

## Additional Investigations Needed

1. Check if there are any admin panels or frontend components that manage media
2. Verify Cloudinary credentials are properly set in environment
3. Check if there are any middleware or interceptors affecting media requests
4. Review any existing media management UI components

