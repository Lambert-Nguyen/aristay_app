### AriStay Management System Delivery Note

Date: 2025-09-11
Environment: Heroku (Production) + Local Dev (PostgreSQL)

#### 1) What’s included
- Backend: Django REST API with JWT security, audit logging, throttling, soft-delete, task automation, booking import with conflict handling
- Web UI: Staff Portal and Manager Console (Django templates + JS)
- Mobile (Flutter): iOS app foundations (models/services; production integration ready)
- Admin: Django Admin for configuration (properties, tasks, users, checklists, inventory)

#### 2) Highlights delivered recently
- Manager/staff visibility model: managers/superusers or team-view profiles see all tasks; staff see only assigned
- Task counts API aligned with visibility scope
- Photo Upload UI fixed to honor property access
- Checklist system restored end-to-end (admin assignment, DRF exposure, staff detail rendering). Auto-backfill of responses where missing
- Charts page reliability: CSP + DOM load fixes; deployed and verified

#### 3) Core capabilities
- Authentication & Roles: Superuser, Manager, Staff/Crew, dynamic permission checks
- Tasks: lifecycle (pending → in-progress → completed), assignment, status updates, history
- Checklists: templates per task type, item responses (text/number/photo), progress tracking
- Photos: before/after upload and comparison per checklist item
- Inventory: lookup and transaction logging
- Lost & Found: report and manage items tied to tasks/properties
- Reports: Manager charts dashboard (Chart.js)
- Booking import: enhanced Excel import with conflict detection (ready to enable)

#### 4) Operational notes
- Database: PostgreSQL (prod + CI). Redis for throttling/caching
- Security: JWT with rotation/blacklist, Axes login protection, CSP headers in production
- Deploys: Heroku app `aristay-internal-backend` from branch `deployment-clean` subdir `aristay_backend`
- Static: `collectstatic` runs on release. Warning: prefer `.python-version` over `runtime.txt` in future

#### 5) Primary URLs (Heroku)
- Staff Dashboard: `/api/staff/`
- Staff Tasks list: `/api/staff/tasks/`
- Staff Task detail: `/api/staff/tasks/<id>/`
- Task counts (AJAX): `/api/staff/task-counts/`
- Task progress (AJAX): `/api/staff/tasks/<id>/progress/`
- Update task status (AJAX): `/api/staff/tasks/<id>/status/`
- Photos: `/api/staff/photos/upload/`, `/api/staff/photos/comparison/<task_id>/`
- Lost & Found: `/api/staff/lost-found/`, `/api/staff/lost-found/create/`
- Inventory Lookup: `/api/staff/inventory/`
- Manager Charts: `/manager/charts/`
- Admin: `/admin/`
- Auth (JWT): `/api/token/`, `/api/token/refresh/`, `/api/token/revoke/`

#### 6) Data model (selected)
- Task ➜ one-to-one TaskChecklist ➜ many ChecklistResponse ➜ many ChecklistPhoto
- ChecklistTemplate ➜ many ChecklistItem
- Property ➜ many Task; Booking ➜ many Task (optional)

