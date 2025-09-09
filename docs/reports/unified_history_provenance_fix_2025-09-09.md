# Unified History & Provenance Fixes Across Models

Date: 2025-09-09
Scope: Django Admin + Staff (Dashboard) unified history for all DRF models with provenance stamping
Status: Completed and verified (pytest CI passing)

## Summary
- Implemented consistent user attribution and source labeling (Admin vs Dashboard) across models.
- Standardized unified history view parsing and ordering by true timestamps.
- Ensured ISO8601 timestamps are parsed reliably and rendered consistently.

## Changes
- Added ProvenanceStampMixin in `api/admin.py` and applied to all admin classes:
  - Stamps `modified_by` (when model has it) and `modified_via` (default: `admin`) on save.
- Refined unified history combiner in `create_unified_history_view()`:
  - Parses custom history strings by partitioning on ": " to avoid breaking ISO times.
  - Extracts actor from "<user> changed ..." safely.
  - Normalizes datetimes to timezone-aware and sorts strictly by timestamp (newest first).
  - Displays consistent, human-readable entries for both Admin (LogEntry) and Dashboard (model.history).
- `LostFoundItem`:
  - Added `modified_by`, `modified_via` fields; history attribution now uses `modified_by`.

## Models Covered
- Task, Property, Booking, PropertyOwnership, Notification
- ChecklistTemplate, ChecklistResponse, TaskChecklist
- InventoryCategory, InventoryItem, PropertyInventory, InventoryTransaction
- LostFoundItem, ScheduleTemplate, GeneratedTask
- BookingImportTemplate, BookingImportLog
- CustomPermission, RolePermission, UserPermissionOverride
- User (via admin class)

## Verification
- Manual checks in Admin history pages (Task, Property, Notification, LostFoundItem):
  - Correct user attribution per source (Admin vs Dashboard).
  - Consistent timestamp formatting; entries ordered by time.
  - Dashboard entries show detailed before/after narratives; Admin entries include Django change messages.
- Staff portal Lost & Found list shows items correctly for found-by user and accessible properties.

## CI / Tests
- Ran `python manage.py check` → no issues.
- Ran `python -m pytest -q` → all tests passed.
- No changes required to existing tests; behavior now aligns with expectations.

## Usage/Notes
- When saving via Admin, provenance is auto-stamped.
- When saving via Dashboard/API views, set `obj.modified_by = request.user` and `obj.modified_via = 'dashboard'` (if models include these fields) before saving to maintain consistent attribution.

## Future Enhancements
- Consider extracting provenance stamping to a model mixin and middleware for API views.
- Add optional pagination for long history lists.
