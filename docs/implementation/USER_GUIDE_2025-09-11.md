### AriStay Management User Guide (Non‑Technical)

Welcome to AriStay Management. This guide helps managers and staff use the system confidently.

#### 1) Signing In
- Go to the login page and enter your username and password.
- After login:
  - Managers go to the Manager Console.
  - Staff go to the Staff Portal.

Endpoints used (for reference): `/api/token/` for API logins; app pages use form login.

#### 2) Staff Portal Overview
- Portal: `/api/staff/` — shows your workspace.
- Navigation:
  - Tasks: view and work on assigned tasks.
  - Inventory: check supplies.
  - Lost & Found: report items.

#### 3) Working with Tasks
- Task List: `/api/staff/tasks/`
  - You’ll see tasks assigned to you. Managers may see all tasks.
- Open a task: click a row to go to `/api/staff/tasks/<id>/`.
  - Header shows property, dates, assignee, and description.
  - Timer: Start to track time on the task.
  - Photos: Upload or view before/after.
  - Status: Start or Complete.

Progress bar updates live based on your checklist.
- The page calls `/api/staff/tasks/<id>/progress/` periodically to refresh counts.
- When you press Start/Complete, it calls `/api/staff/tasks/<id>/status/`.

#### 4) Checklists (Your step‑by‑step)
- Many tasks include a checklist of steps (e.g., room cleaning, maintenance checks).
- Each line can be:
  - Checkbox (mark done)
  - Text or Number input
  - Photo required (upload images)
- Tips:
  - Required items have an asterisk (*).
  - Photo buttons appear only when photos are useful or required.
  - Notes can be added to any checklist item.

If a task has a template but no steps yet, the system now auto‑fills the steps.

#### 5) Uploading Photos
- On a task, click “Upload Photos”.
- Or, within a checklist item with photos, click “Add Photos”.
- The system validates type and size (max ~5MB each).

Related endpoints: `/api/staff/checklist/photo/upload/`, `/api/staff/checklist/photo/remove/`.

#### 6) Lost & Found
- From the task detail, click “Report Lost & Found”.
- Fill in the title, description, where it was found, and optional notes.
- After saving, you can review items in `/api/staff/lost-found/`.

Create endpoint: `/api/staff/lost-found/create/`.

#### 7) Inventory
- Use `/api/staff/inventory/` to look up items and quantities.
- Managers can record transactions (add/remove stock) where enabled.

Transaction endpoint: `/api/staff/inventory/transaction/`.

#### 8) Manager Console
- Charts and reports at `/manager/charts/`.
- See workload, completion rates, overdue tasks, and trends.

Managers and superusers can see team‑wide tasks and counts; staff see only what’s assigned to them.

#### 9) Admin (for configuration)
- Go to `/admin/` to manage:
  - Properties
  - Tasks
  - Checklist Templates and Items
  - Users and permissions
  - Inventory catalogs

Assigning a checklist template:
- Open a Task in Admin, use the “Task checklist” inline to pick a template.
- The system auto‑creates step responses so staff can work immediately.

#### 10) Helpful Notes
- If a checklist looks empty, refresh the page once; steps should appear.
- Undefined% on progress means the page hadn’t received data yet; it now shows 0% until data loads.
- If a staff member needs to see all tasks, ask a manager to grant "team view" access or change role to Manager.

#### 11) API Quick Reference (for integrators)
- Auth: `/api/token/`, `/api/token/refresh/`, `/api/token/revoke/`
- Staff:
  - `/api/staff/tasks/` (list) | `/api/staff/tasks/<id>/` (detail)
  - `/api/staff/tasks/<id>/status/` (POST)
  - `/api/staff/tasks/<id>/progress/` (GET)
  - `/api/staff/task-counts/` (GET)
  - Checklist item update: `/api/staff/checklist/<item_id>/update/` (POST)
  - Photos: `/api/staff/checklist/photo/upload/` (POST), `/api/staff/checklist/photo/remove/` (POST)
  - Lost & Found: `/api/staff/lost-found/` (GET), `/api/staff/lost-found/create/` (POST)
  - Photos UI: `/api/staff/photos/upload/`, `/api/staff/photos/comparison/<task_id>/`
- Manager reports: `/manager/charts/`
- Admin: `/admin/`

#### 12) Support
- If you forget your password, contact your manager or system admin.
- For issues with photos or checklists not showing, refresh once; if it persists, note the task ID and report it.
