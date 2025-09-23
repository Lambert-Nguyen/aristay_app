## Unified Checklist + Task Photo System

### Overview
Checklist photos are now unified with the task before/after photo system via `TaskImage`.

### Data Model Changes
- `TaskImage`:
  - Added `photo_type='checklist'` option
  - Added optional `checklist_response` FK linking images to a `ChecklistResponse`
  - Indexed `checklist_response`

### API/View Changes
- `api/staff_views.upload_checklist_photo` now creates `TaskImage` with:
  - `task` = parent task
  - `photo_type='checklist'`
  - `sequence_number` auto-incremented per task/type
  - `checklist_response` = the response being updated
- `api/staff_views.remove_checklist_photo` now removes the corresponding `TaskImage`; falls back to legacy `ChecklistPhoto` for older records.

### Templates
- `api/templates/staff/task_detail.html` renders `response.unified_photos` (from `TaskImage`) instead of legacy `response.photos`.

### Migration
- `api/migrations/0070_unify_checklist_photos_into_taskimage.py`
  - Backfills existing `ChecklistPhoto` into `TaskImage` linked via `checklist_response` and parent `task`.
  - Marks imported photos as `photo_status='approved'` and copies caption to `description`.

### Serializer
- `TaskImageSerializer` now exposes `checklist_response` for UI wiring.

### Usage
1. Upload checklist photo via staff UI → creates `TaskImage(photo_type='checklist')`.
2. All task photos (before/after/checklist) appear together in task contexts.
3. Removing a checklist photo removes the `TaskImage`.

### Deployment Steps
1. Run database migrations:
   - `python manage.py migrate`
2. Verify unified UI:
   - Open a task with a checklist and upload/remove photos
3. Optional: remove legacy references to `ChecklistPhoto` once data verified.

### Tests
- Added cases ensuring upload creates `TaskImage` and removal deletes it (`tests/api/test_task_image_api.py`).

### Notes
- Legacy `ChecklistPhoto` model remains temporarily for compatibility. New uploads go solely to `TaskImage`.


