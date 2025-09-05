# Aristay App

**Aristay** is a cleaning & maintenance management system for property managers.  
It consists of a Flutter mobile frontend and a Django REST backend secured by token auth.  
Users can sign up, log in, browse, filter and manage cleaning/maintenance tasks—complete with photos, history, and per-user timezones.

---

## 🏆 Features

### Authentication & Users
- **Token-based login/registration** via Django REST Framework's `authtoken`.
- **Dynamic permission system** with role-based access control (Superuser, Manager, Staff, Viewer).
- **User permission overrides** with expiration dates and delegation capabilities.
- **`/api/users/me/`**: Fetch or PATCH your own profile (e.g. `timezone`).
- **Admin**:  
  - Inline **Profile** (stores `timezone`) on the User admin page.  
  - Visible `timezone` column in the user list.  
  - Invite users & reset passwords via admin endpoints.
  - Permission management interface.

### Task Management
- **CRUD** tasks with fields:  
  - **Property**, **type** (cleaning/maintenance), **title**, **description**, **status**, **assignee**, **creator**, **modified-by**, **history**, **timestamps**.
- **Photo attachments**: upload, display, delete & replace images per task.
- **Pagination** + “Load More” on task lists.
- **Advanced filters**:  
  - **Search** (title/description), **status**, **property**, **assignee**, **date range**, **overdue** (due < now & not completed/canceled).
- **“All (##)”** quick-reset button in the UI.  
- **Timezone awareness**:  
  - All date/time fields are stored in UTC and displayed in the user’s local timezone.

---

## 🛠 Tech Stack

- **Frontend**  
  - Flutter & Dart  
  - `http`, `shared_preferences`, `image_picker`, `intl`  
- **Backend**  
  - Django & Django REST Framework  
  - SQLite (dev) / PostgreSQL (prod)  
  - `django-filter` for advanced filtering  
- **Auth**  
  - DRF TokenAuthentication  
- **Deployment**  
  - Ready for AWS / any cost-effective cloud

---

## 🚀 Installation & Setup

### 1. Backend (Django)

1. **Clone & enter the backend repo:**
   ```bash
   git clone <repo-url> aristay_backend
   cd aristay_backend
2. **Create & activate a Python virtualenv:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
4. **Apply migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
5. **Set up permissions system:**
   ```bash
   python manage.py setup_permissions
6. **Create a superuser (for admin UI):**
   ```bash
   python manage.py createsuperuser
7. **Run the dev server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000

## New API Endpoints
   •	PATCH /api/users/me/
   ```bash
   { "timezone": "America/Los_Angeles" }
   ```
   •	GET /api/tasks/?overdue=true
   ```bash
   Returns tasks whose due date is past and status ≠ completed/canceled.
   ```

### Frontend (Flutter)

1. **Clone & enter the Flutter repo:**
   ```bash
   git clone <repo-url> aristay_flutter_frontend
   cd aristay_flutter_frontend
3. **Install Flutter dependencies:**
      ```bash
   flutter clean
   flutter pub get
4. **Run on your device or simulator:**
      ```bash
   flutter run
5. **Routes of interest**
      ```bash
   '/':            LoginScreen
   '/home':        HomeScreen
   '/tasks':       TaskListScreen
   '/settings':    SettingsScreen   // stub for timezone chooser
   '/create-task': TaskFormScreen
   '/edit-task':   EditTaskScreen
   '/task-detail': TaskDetailScreen
   // Admin:
   '/admin/users'
   '/admin/invite'
   '/admin/reset-password'
   '/admin/create-user'
   ```

## 📖 Usage
	1.	Log in with your credentials (or register via API/admin).
	2.	Browse tasks at Tasks → All / Status toggles / Overdue.
	3.	Search (tap the 🔍 icon) or filter (🔎 icon) for properties, assignees, date ranges, or overdue tasks.
	4.	Create/Edit tasks and attach photos.
	5.	View details: zoomable photos, history, timestamps in your local timezone.
	6.	Settings (coming soon): choose your preferred timezone.

## Contributing

Nguyen, Phuong Duy Lam

## License

This project is licensed under the MIT License.
