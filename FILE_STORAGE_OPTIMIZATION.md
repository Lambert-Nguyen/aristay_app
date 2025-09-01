# Excel Import File Storage Optimization Solutions

## Problem Statement
The Excel import system saves every uploaded file to `aristay_backend/media/booking_imports/YYYY/MM/`, which causes disk space to grow indefinitely over time.

## Current Storage Status
- **Total Files**: 19
- **Total Size**: 5.7 MB
- **Current Impact**: Low (still manageable)
- **Growth Pattern**: Will scale linearly with import frequency

## 🛠️ Implemented Solutions

### 1. Management Command (`cleanup_imports`)
**Location**: `api/management/commands/cleanup_imports.py`

**Usage Examples**:
```bash
# Show current storage statistics
python manage.py cleanup_imports --stats

# Show cleanup suggestions to stay under 100MB
python manage.py cleanup_imports --suggest 100

# See what would be deleted (dry run)
python manage.py cleanup_imports --days 30 --dry-run

# Actually delete files older than 30 days
python manage.py cleanup_imports --days 30
```

**Features**:
- ✅ Storage statistics with file counts and sizes
- ✅ Smart cleanup suggestions based on target size
- ✅ Dry-run mode to preview deletions
- ✅ Time-based cleanup (keep last N days)
- ✅ Safe deletion (removes files but preserves import logs)

### 2. Cleanup Service (`ImportFileCleanupService`)
**Location**: `api/services/file_cleanup_service.py`

**Methods**:
- `cleanup_old_files(days, dry_run)` - Remove files older than N days
- `get_storage_stats()` - Current storage information
- `suggest_cleanup(target_mb)` - Intelligent cleanup recommendations

**Features**:
- ✅ Programmatic access for automation
- ✅ Error handling and logging
- ✅ Human-readable size formatting
- ✅ Database cleanup (removes file references safely)

### 3. REST API Endpoint
**Location**: `api/views.py` → `file_cleanup_api`
**URL**: `/api/file-cleanup/api/`

**Usage Examples**:
```bash
# Get storage stats
curl -X GET /api/file-cleanup/api/ -H "Authorization: Token YOUR_TOKEN"

# Get cleanup suggestions
curl -X POST /api/file-cleanup/api/ \
  -d "action=suggest&target_mb=50" \
  -H "Authorization: Token YOUR_TOKEN"

# Dry run cleanup
curl -X POST /api/file-cleanup/api/ \
  -d "action=dry_run&days=30" \
  -H "Authorization: Token YOUR_TOKEN"

# Actually cleanup files
curl -X POST /api/file-cleanup/api/ \
  -d "action=cleanup&days=30" \
  -H "Authorization: Token YOUR_TOKEN"
```

### 4. Automated Cron Script
**Location**: `cleanup_cron.py`

**Setup Instructions**:
```bash
# Add to crontab for weekly cleanup (Sundays at 2 AM)
0 2 * * 0 cd /path/to/aristay_backend && python cleanup_cron.py --days 30

# Add to crontab for daily size-based cleanup (1 AM daily)
0 1 * * * cd /path/to/aristay_backend && python cleanup_cron.py --target-mb 50
```

**Features**:
- ✅ Logging to `logs/file_cleanup.log`
- ✅ Email notifications on errors (if configured)
- ✅ Multiple cleanup strategies (time-based vs size-based)
- ✅ Safe error handling

## 📋 Recommended Usage Strategies

### Strategy 1: Time-Based Cleanup (Recommended)
Keep files for a fixed period, then automatically delete them.

```bash
# Keep last 30 days, run weekly
0 2 * * 0 cd /path/to/aristay_backend && python manage.py cleanup_imports --days 30
```

**Pros**: Predictable, simple, good for compliance
**Cons**: Disk usage can vary

### Strategy 2: Size-Based Cleanup
Dynamically adjust retention to stay under a target size.

```bash
# Keep under 100MB, run daily
0 1 * * * cd /path/to/aristay_backend && python cleanup_cron.py --target-mb 100
```

**Pros**: Predictable disk usage
**Cons**: Retention period varies

### Strategy 3: Hybrid Approach
Combine both strategies for optimal results.

```bash
# Size check daily, minimum 7 days retention
0 1 * * * cd /path/to/aristay_backend && python cleanup_cron.py --target-mb 100
# Time-based weekly cleanup as backup
0 2 * * 0 cd /path/to/aristay_backend && python manage.py cleanup_imports --days 90
```

## 🔧 Advanced Configuration Options

### Custom Cleanup Policy
Edit `api/services/file_cleanup_service.py` to add custom logic:

```python
def custom_cleanup_policy(self):
    """Example: Keep important files longer"""
    # Keep high-success imports longer
    # Delete error-prone imports sooner
    # Preserve files from specific users
```

### Integration with Cloud Storage
For long-term archival before deletion:

```python
def archive_to_cloud_before_delete(self, file_path):
    # Upload to AWS S3, Google Cloud, etc.
    # Then delete local copy
```

### Monitoring Integration
Add alerts when storage grows too large:

```python
def check_storage_alerts(self):
    stats = self.get_storage_stats()
    if stats['total_size_mb'] > 500:  # Alert threshold
        send_alert("Storage exceeds 500MB")
```

## 📊 Monitoring Commands

```bash
# Daily storage check
python manage.py cleanup_imports --stats

# Weekly detailed analysis
python manage.py cleanup_imports --suggest 100

# Monthly trend analysis (custom script needed)
python analyze_storage_trends.py
```

## 🚨 Safety Features

### Backup Before Cleanup
```bash
# Create backup before major cleanup
python manage.py dumpdata api.BookingImportLog > backup_import_logs.json
python manage.py cleanup_imports --days 30
```

### Rollback Capability
The system preserves `BookingImportLog` records even after file deletion, so import history is maintained.

## 🎯 Next Steps

1. **Choose Strategy**: Decide between time-based, size-based, or hybrid approach
2. **Set Up Automation**: Add chosen cleanup script to crontab
3. **Monitor**: Set up alerts for storage growth
4. **Document**: Update deployment documentation with cleanup procedures
5. **Test**: Run dry-run cleanups regularly to verify expected behavior

## 💡 Alternative Solutions (Future)

### Cloud Storage Migration
- Move old files to S3/Google Cloud after N days
- Keep local files for recent imports only
- Reduces local disk usage while maintaining access

### Database Optimization
- Store only essential Excel data in database
- Use file references instead of storing full Excel content
- Implement lazy loading for file access

### Compression
- Compress old Excel files before archival
- Use ZIP compression for batch cleanup
- Can reduce storage by 60-80%

---

**Current Status**: ✅ All solutions implemented and tested
**Immediate Action Needed**: Choose and implement automation strategy
**Estimated Setup Time**: 15 minutes for basic automation
