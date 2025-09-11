## Task Groups: Staff Assignment and Dashboard Permissions

This document describes the Task Group capability added to AriStay for assigning staff/crew to departments and scoping dashboard permissions.

### Overview
- Purpose: Segment staff into functional groups for visibility and permissions
- Groups: cleaning, maintenance, laundry, lawn_pool, general, none
- Affects: Django models, admin, API serialization, permissions, and a management command

### Model Changes
- File: `aristay_backend/api/models.py`
- Enum: `TaskGroup(models.TextChoices)` with values:
  - cleaning, maintenance, laundry, lawn_pool, general, none
- Field: `Profile.task_group: CharField(choices=TaskGroup.choices, default=TaskGroup.NONE)`
- Helper methods on `Profile`:
  - `get_task_group_display()` → human name
  - `is_in_task_group(task_group)` → membership check (accepts enum or string)
  - `can_view_task_group(task_group)`:
    - Superuser/Manager → can view all
    - Staff → own group + general
    - Viewer → all only if `can_view_other_teams=True`
  - `get_accessible_task_groups()` returns a list of `TaskGroup` enums:
    - Superuser/Manager → all except NONE
    - Staff(NONE) → [GENERAL]
    - Staff(non-GENERAL) → [own, GENERAL]
    - Viewer(with other teams) → all except NONE; else []

### Signals and Defaults
- Post-save signal creates/syncs `Profile` for a `User` if missing
- Default role: SUPERUSER if `user.is_superuser` else STAFF
- Default `task_group`: `TaskGroup.NONE`

### Admin UI
- Files:
  - `aristay_backend/api/admin.py`
  - `aristay_backend/api/managersite.py`
- Add `task_group` to `ProfileInline` fields
- Show task group in `list_display` via `get_task_group`
- Add list filter on `profile__task_group` in manager admin

### API Serialization
- File: `aristay_backend/api/serializers.py`
- `UserSerializer` includes `task_group` via `get_task_group()`, returns enum value string or 'none'

### Management Command
- File: `aristay_backend/api/management/commands/assign_task_groups.py`
- Purpose: Assign task groups in bulk or individually
- Options:
  - `--list-groups` → list available groups
  - `--show-users` → list users with current task groups
  - `--auto-assign` → assign based on Django groups/roles (staff default to general)
  - `--username <user> --task-group <group>` → manual assign
- Examples:
  - List: `python -m manage assign_task_groups --list-groups`
  - Show: `python -m manage assign_task_groups --show-users`
  - Auto: `python -m manage assign_task_groups --auto-assign`
  - Manual: `python -m manage assign_task_groups --username alice --task-group cleaning`

Note: When calling via Django directly, use `python aristay_backend/manage.py assign_task_groups ...` from project root.

### Migrations
- Files:
  - `aristay_backend/api/migrations/0064_add_task_group_to_profile.py`
  - `aristay_backend/api/migrations/0065_booking_booking_no_overlap_active.py`
- PostgreSQL-only constraints are wrapped with `connection.vendor == 'postgresql'` guards to keep SQLite tests green.

### Permissions Behavior Summary
- Superuser/Manager: full access to all groups (except NONE in listings)
- Staff: own group + general; NONE implies only general
- Viewer: needs `can_view_other_teams=True` to access any groups

### Testing
- Files:
  - `tests/unit/test_task_group_functionality.py` (12 tests)
  - `tests/unit/test_assign_task_groups_command.py` (11 tests)
  - Updated: `tests/permissions/test_dynamic_permissions.py`, `tests/ui/test_nav_visibility.py`
- Notes:
  - Tests use `Profile.objects.get_or_create(...)` to avoid conflicts with the post-save signal
  - Assertions use `TaskGroup` enums for return lists where applicable

### Rollout / Safety
- Backward compatible: default NONE keeps prior behavior until assignments are made
- Admin can assign group per user; command supports bulk assignment
- Ensure environment vars, migrations, and `ALLOWED_HOSTS` are set for devices when testing on mobile

### Troubleshooting
- IntegrityError on Profile creation in tests: use `get_or_create` (signal already creates Profile)
- Mixed enum/string comparisons: methods accept both, but return enums in `get_accessible_task_groups()`
- CI flakiness from cross-test users: tests updated to be resilient to pre-existing users


