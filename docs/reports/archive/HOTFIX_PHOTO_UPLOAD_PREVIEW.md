# Photo Upload Preview Hotfix - 2025-10-13

## Issues Fixed

### 1. ✅ Photo Preview Not Showing (CSP Violation)
**Problem**: Blob URLs blocked by Content Security Policy
```
Refused to load the image 'blob:https://aristay-internal.cloud/...' 
because it violates the following Content Security Policy directive: "img-src 'self' data: https:".
```

**Fix**: Updated CSP in `api/enhanced_security_middleware.py`
```python
# Before
"img-src 'self' data: https:; "

# After  
"img-src 'self' data: https: blob:; "
```

**Impact**: Photo previews now display correctly when uploading

---

### 2. ✅ Duplicate Variable Declaration
**Problem**: `touchStartX` declared twice causing SyntaxError
```
Uncaught SyntaxError: Identifier 'touchStartX' has already been declared
```

**Fix**: Removed duplicate declaration in `api/templates/staff/base.html`
- Line 810: First declaration (for secret message swipe)
- Line 927: Removed duplicate, now reuses variable from line 810
- Added `{ passive: true }` for better mobile performance

**Impact**: No more JavaScript errors, improved touch gesture handling

---

### 3. ⚠️ 404 Image Error (Existing Issue)
**Problem**: One image returns 404
```
GET https://res.cloudinary.com/dz5jblgfs/image/upload/v1/media/task_images/34/94706c1949a741a2a1c280aea802940d_aarejn 404
```

**Status**: This is a data issue - the image was deleted from Cloudinary but the database record still exists.

**Recommendation**: Run cleanup command:
```bash
python manage.py cleanup_broken_photos --dry-run
python manage.py cleanup_broken_photos  # to actually delete
```

---

### 4. ℹ️ Font CSP Warning (Non-Critical)
**Problem**: External font blocked
```
Refused to load the font 'https://r2cdn.perplexity.ai/fonts/FKGroteskNeue.woff2'
```

**Status**: This is expected behavior - external fonts are blocked for security. The app uses fallback fonts.

**Impact**: None - fallback fonts work correctly

---

## Files Modified

1. `aristay_backend/api/enhanced_security_middleware.py`
   - Added `blob:` to CSP `img-src` directive

2. `aristay_backend/api/templates/staff/base.html`
   - Removed duplicate `touchStartX` declaration
   - Added passive event listeners for better performance

---

## Testing Checklist

- [x] Photo preview displays when uploading
- [x] No JavaScript console errors
- [x] Touch gestures work on mobile
- [x] Existing photos load correctly
- [ ] Run cleanup command for broken images (recommended)

---

## Deployment Notes

**Branch**: `deployment-clean`
**Environment**: Heroku (auto-deploy)
**Risk Level**: LOW - Only CSP and JS fixes, no database changes

**Post-Deployment**:
1. Test photo upload on production
2. Verify no console errors
3. Optional: Run `cleanup_broken_photos` command

---

## Related Issues

- Original issue: #40 (Unified Photo System)
- Photo management: Implemented in previous PRs
- Cleanup command: Already exists in `api/management/commands/`

