# Aristay App

Aristay App is a cleaning and maintenance management application designed for property management. It features a Flutter-based mobile frontend and a Django-based backend secured with token authentication. This project allows users to register, log in, and manage cleaning tasks with detailed views and ownership-based editing.

## Features

- **User Registration & Authentication:**  
  - Secure token-based authentication (Django REST Framework's authtoken).
  - User registration API endpoint.
- **Task Management:**  
  - Create, read, update, and delete cleaning tasks.
  - Task details include property name, status, creator, assignee, and history.
  - Only task owners (or admins) can edit or delete their tasks.
  - Paginated task list with "Load More" functionality.
- **Frontend:**  
  - Built with Flutter (Dart) for iOS (and optionally Android).
  - Clean UI for login, task listing, task detail, and task creation/editing.
- **Backend:**  
  - Built with Django and Django REST Framework.
  - Uses a SQLite database for development (recommended PostgreSQL for production).
- **Deployment:**  
  - Ready for cost-effective deployment on AWS or similar cloud services.

## Tech Stack

- **Frontend:** Flutter (Dart)
- **Backend:** Django, Django REST Framework (Python)
- **Authentication:** Token Authentication
- **Database:** SQLite (development) / PostgreSQL (production recommended)
- **Deployment:** AWS (or other cost-effective cloud solutions)

## Installation and Setup

### Frontend (Flutter)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd aristay_flutter_frontend
2. **Install Flutter dependencies:**
   flutter pub get
3. **Run the app on your desired device or simulator:**
   flutter run

### Backend (Django)

1. **Clone the repository:**
   git clone <repository-url>
   cd aristay_backend
2. **Create and activate a virtual environment:**
   python3 -m venv venv
   source venv/bin/activate
3. **Install Python dependencies:**
   pip install -r requirements.txt
4. **Apply database migrations:**
   python manage.py makemigrations
   python manage.py migrate
5. **Run the development server:**
   python manage.py runserver 0.0.0.0:8000

## Contributing

Nguyen, Phuong Duy Lam

## License

This project is licensed under the MIT License.