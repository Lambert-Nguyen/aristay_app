# Enhanced Excel Import with Conflict Resolution - Integration Guide

## Overview

The Enhanced Excel Import Service provides intelligent conflict detection and resolution for booking imports, with different handling for platform vs direct bookings.

## Key Features

### 🤖 Smart Conflict Detection
- **Platform Bookings (Airbnb, VRBO)**: Auto-update existing bookings
- **Direct/Owner Bookings**: Require manual review for conflicts
- **Confidence Scoring**: AI-powered matching confidence (0.0 - 1.0)
- **Conflict Types**: Date changes, guest changes, status changes, property changes

### 🎯 Conflict Resolution Interface
- **Visual Comparison**: Side-by-side view of existing vs Excel data
- **Bulk Actions**: Resolve multiple conflicts at once
- **Preview Mode**: See changes before applying them
- **Mobile Responsive**: Works on tablets and phones

### 📊 Audit Trail
- **Complete History**: All import decisions are logged
- **Session Management**: Each import gets a unique session ID
- **Error Tracking**: Detailed error logs with row-level information

## File Structure

```
api/
├── services/
│   ├── excel_import_service.py          # Original service (unchanged)
│   └── enhanced_excel_import_service.py # New enhanced service
├── views/
│   ├── conflict_resolution_views.py     # Conflict resolution UI
│   └── enhanced_excel_import_view.py    # Enhanced import interface
└── templates/admin/
    ├── enhanced_excel_import.html       # Enhanced import form
    └── conflict_resolution.html         # Conflict resolution UI
```

## How It Works

### 1. Enhanced Import Process

```python
# Use the enhanced service instead of the original
from api.services.enhanced_excel_import_service import EnhancedExcelImportService

service = EnhancedExcelImportService(request.user)
result = service.import_excel_file(excel_file, sheet_name)

if result['requires_review']:
    # Redirect to conflict resolution
    return redirect('conflict-review', result['import_session_id'])
```

### 2. Conflict Detection Logic

```python
# Platform bookings (auto-resolve)
if source in ['airbnb', 'vrbo'] and external_code_matches:
    return auto_update_booking()

# Direct bookings (manual review)
if source == 'direct' or guest_name_matches:
    return require_manual_review()
```

### 3. Conflict Resolution API

```javascript
// Resolve conflicts via AJAX
fetch('/api/conflicts/{session_id}/resolve/', {
    method: 'POST',
    body: JSON.stringify({
        resolutions: [{
            conflict_index: 0,
            action: 'update_existing',  // or 'create_new', 'skip'
            apply_changes: ['guest_name', 'dates', 'status']
        }]
    })
})
```

## Integration Steps

### 1. Add URLs to your project

```python
# In api/urls.py - already added
path('enhanced-excel-import/', enhanced_excel_import_view, name='enhanced-excel-import'),
path('admin/conflicts/<int:import_session_id>/', ConflictReviewView.as_view(), name='conflict-review'),
```

### 2. Update Admin Interface

Add link to enhanced import in your admin:

```html
<a href="{% url 'enhanced-excel-import' %}">📊 Enhanced Excel Import</a>
```

### 3. Database Migration (if needed)

No additional database changes required - uses existing models.

## Usage Instructions

### For Managers

1. **Access**: Navigate to `/enhanced-excel-import/`
2. **Upload**: Drag & drop or select Excel file
3. **Process**: Click "Start Enhanced Import"
4. **Review**: If conflicts detected, review and resolve them
5. **Complete**: All bookings processed with full audit trail

### For Developers

```python
# Basic usage
service = EnhancedExcelImportService(user)
result = service.import_excel_file(file, 'Cleaning schedule')

# Check for conflicts
if result['requires_review']:
    conflicts = result['conflicts']
    session_id = result['import_session_id']
    
    # Use ConflictResolutionService to resolve
    resolver = ConflictResolutionService(user)
    resolver.resolve_conflicts(session_id, resolutions)
```

## Testing

Run the test script to verify functionality:

```bash
cd aristay_backend
python test_enhanced_excel_import.py
```

## API Endpoints

### Import Endpoints
- `POST /enhanced-excel-import/api/` - Enhanced import API
- `GET /enhanced-excel-import/` - Import form interface

### Conflict Resolution Endpoints
- `GET /admin/conflicts/{session_id}/` - Conflict review interface
- `POST /api/conflicts/{session_id}/resolve/` - Resolve conflicts
- `GET /api/conflicts/{session_id}/details/` - Get conflict details
- `GET /admin/conflicts/{session_id}/preview/{conflict_index}/` - Preview resolution

## Error Handling

The service handles errors gracefully:

```python
try:
    result = service.import_excel_file(file)
    if result['success']:
        # Handle success and conflicts
    else:
        # Handle import errors
        errors = result['errors']
except Exception as e:
    # Handle service exceptions
    logger.error(f"Import failed: {e}")
```

## Performance Considerations

- **Memory**: Processes Excel files row-by-row to handle large files
- **Database**: Uses bulk operations where possible
- **Caching**: Conflict data stored in import log for session management
- **Mobile**: Responsive design works on all devices

## Security

- **Authentication**: All endpoints require login
- **Staff Access**: Import functions require staff permissions
- **CSRF Protection**: All forms include CSRF tokens
- **File Validation**: Excel files validated before processing

## Future Enhancements

1. **AI Confidence Tuning**: Machine learning to improve match confidence
2. **Bulk Resolution Rules**: Save resolution patterns for future imports
3. **Integration APIs**: Connect with external booking platforms
4. **Advanced Reporting**: Detailed analytics on import patterns

## Support

For issues or questions:
1. Check the import logs in Django admin
2. Review error messages in the conflict resolution interface
3. Enable debug logging for detailed troubleshooting

## Conclusion

The Enhanced Excel Import Service provides a robust, user-friendly solution for managing booking imports with intelligent conflict detection and resolution. It maintains backward compatibility while adding powerful new features for production deployment.
