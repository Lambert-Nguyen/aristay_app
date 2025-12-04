# 🏨 Aristay - Property Management System

**Aristay** is a comprehensive property management platform designed for modern hospitality operations. It features a robust Django REST API backend with JWT authentication, automated task management, and a Flutter mobile application for on-the-go property management.

## 🎯 Project Overview

### Core Features
- 🔐 **JWT Authentication** - Secure, token-based authentication system
- 📋 **Booking Management** - Comprehensive reservation and guest management
- 🤖 **Task Automation** - Automated cleaning and maintenance task creation
- 👥 **Role-Based Access Control** - Granular permission system
- 💬 **Real-Time Chat** - WebSocket-based messaging system with Django Channels
- 📱 **Mobile Application** - Flutter-based mobile interface
- 📊 **Admin Dashboard** - Staff management and reporting interface
- 📸 **Photo Management** - Before/after photo tracking and approval workflow
- 📅 **Calendar System** - Property and task scheduling interface

### Technology Stack
- **Backend**: Django REST Framework with PostgreSQL
- **Real-Time**: Django Channels with Redis for WebSocket support
- **Frontend**: Flutter mobile application
- **Web UI**: Django templates with modern JavaScript
- **Authentication**: JWT with djangorestframework-simplejwt
- **Testing**: Comprehensive test suite with pytest
- **Deployment**: Production-ready with security hardening

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with virtual environment
- Node.js and Flutter SDK
- PostgreSQL database
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd aristay_app

# Set up backend environment
cd aristay_backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Flutter Mobile App Setup
```bash
# Navigate to Flutter directory
cd aristay_flutter_frontend

# Install dependencies
flutter pub get

# Run the app
flutter run
```

## 📚 Documentation

All project documentation is comprehensively organized in the [`docs/`](docs/) directory:

### 📋 Essential Documentation
- **[CLEANUP_PLAN.md](CLEANUP_PLAN.md)** - Project organization and cleanup strategy
- **[PROJECT_CLEANUP_SUMMARY.md](PROJECT_CLEANUP_SUMMARY.md)** - Recent reorganization summary
- **[docs/CURRENT_DOCUMENTATION.md](docs/CURRENT_DOCUMENTATION.md)** - ⭐ Quick reference to active docs
- **[docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** - Complete documentation catalog

### 🔗 Quick Links
- **Setup**: [Deployment Guide](docs/setup/DEPLOYMENT_GUIDE.md) | [Environment Config](docs/backend/ENVIRONMENT_CONFIGURATION.md)
- **Features**: [Chat System](docs/features/chat/CHAT_SYSTEM_QUICKSTART.md) | [Calendar](docs/features/calendar_user_guide.md) | [Photo Management](docs/features/BEFORE_AFTER_PHOTO_QUICK_REFERENCE.md)
- **Security**: [JWT Authentication](docs/security/JWT_AUTHENTICATION_GUIDE.md) | [Security Guide](docs/security/ENHANCED_SECURITY_IMPLEMENTATION.md)
- **Testing**: [Testing Strategy](docs/testing/TESTING_STRATEGY.md) | [Test Organization](docs/testing/TEST_ORGANIZATION.md)
- **Development**: [Local Setup](docs/development/LOCAL_DEVELOPMENT_SETUP.md) | [Project Structure](docs/development/PROJECT_STRUCTURE.md)

## 🧪 Testing

The project includes a comprehensive test suite organized by scope and purpose:

```bash
# Run all tests using the central test runner
python tests/run_tests.py

# Quick system validation
./scripts/testing/quick_test.sh

# JWT authentication testing
./scripts/testing/jwt_smoke_test_improved.sh

# Specific test categories
python tests/run_tests.py --production
python tests/run_tests.py --integration
python tests/run_tests.py --security
```

### Test Categories
- **Unit Tests**: Component-specific validation
- **Integration Tests**: Multi-component workflows
- **Security Tests**: Authentication and authorization
- **Production Tests**: Production readiness validation
- **API Tests**: Endpoint functionality testing

## 🔧 Development Scripts

All development and administrative scripts are organized in [`scripts/`](scripts/):

```bash
# Testing scripts
scripts/testing/quick_test.sh              # Comprehensive test runner
scripts/testing/jwt_smoke_test.sh          # JWT validation

# Administrative scripts  
scripts/admin/audit_user_access.py         # User access audit
scripts/admin/seed_new_permissions.py      # Permission seeding
```

## 🔐 Security Features

Aristay implements enterprise-grade security:

- **JWT Authentication** with refresh tokens and secure headers
- **Rate Limiting** with redis-based throttling
- **Role-Based Permissions** with granular access control
- **API Security** with CORS, CSRF protection, and input validation
- **Production Hardening** with security headers and monitoring

For detailed security information, see the [Security Documentation](docs/security/).

## 🏗️ Project Structure

```
aristay_app/
├── README.md                      # This file
├── CLEANUP_PLAN.md                # Project organization strategy
├── PROJECT_CLEANUP_SUMMARY.md     # Reorganization summary
├── conftest.py                    # Global pytest configuration
├── pytest.ini                     # Test configuration
├── requirements.txt               # Python dependencies
├── aristay_backend/               # Django REST API
│   ├── api/                       # API application
│   │   ├── models_chat.py        # Chat models
│   │   ├── views_chat.py         # Chat views
│   │   ├── consumers.py          # WebSocket consumers
│   │   └── templates/chat/       # Chat UI templates
│   ├── backend/                   # Django settings
│   └── manage.py                  # Django management
├── aristay_flutter_frontend/      # Flutter mobile app
├── tests/                         # Comprehensive test suite
│   ├── api/                       # API tests
│   ├── chat/                      # Chat system tests
│   ├── ui/                        # UI tests
│   ├── backend/                   # Backend tests
│   ├── archive/                   # Archived legacy tests
│   └── utils/                     # Test utilities
├── docs/                          # Complete documentation
│   ├── CURRENT_DOCUMENTATION.md   # ⭐ Quick reference
│   ├── features/chat/             # Chat documentation
│   ├── archive/                   # Historical docs
│   └── reports/archive/           # Old reports
├── scripts/                       # Development & admin scripts
└── tools/                         # Development utilities
    ├── diagnostics/               # Debug tools
    └── secret-hygiene/            # Security scanning
```

See [CLEANUP_PLAN.md](CLEANUP_PLAN.md) for the complete reorganization details.

## 📊 Project Status

✅ **Production Ready** - All core features implemented and tested
✅ **Security Hardened** - Comprehensive security implementation
✅ **Well Documented** - Complete documentation and guides
✅ **Fully Tested** - Comprehensive test coverage
✅ **Organized Structure** - Professional project organization (Nov 2025)
✅ **Chat System** - Real-time messaging with WebSocket support
✅ **Clean Codebase** - 60+ files reorganized for maintainability

### Recent Updates (November 2025)
- ✨ Fixed chat UI authentication and error handling
- 🗂️ Major project reorganization (60 files)
- 📚 Improved documentation structure
- 🧪 Centralized all tests
- 🔧 Fixed .gitignore configuration

For detailed status information, see [PROJECT_CLEANUP_SUMMARY.md](PROJECT_CLEANUP_SUMMARY.md).

## 🤝 Development Workflow

### For New Features
1. Review [Development Setup](docs/development/DEVELOPMENT_SETUP.md)
2. Follow [Coding Standards](docs/development/CODING_STANDARDS.md)
3. Add comprehensive tests
4. Update documentation
5. Run full test suite

### For Bug Fixes  
1. Reproduce issue with test case
2. Implement fix following coding standards
3. Verify fix with all relevant tests
4. Update documentation if needed

### For Security Changes
1. Review [Security Checklist](docs/security/SECURITY_CHECKLIST.md)
2. Implement changes with security focus
3. Run security-focused tests
4. Document security implications

## 📈 Performance & Scalability

- **Database Optimization**: Efficient queries with proper indexing
- **API Performance**: Optimized endpoints with caching
- **Mobile Performance**: Efficient Flutter implementation
- **Scalable Architecture**: Modular design for growth

## 🆘 Support & Troubleshooting

### Common Issues
- **Environment Setup**: See [Installation Guide](docs/setup/INSTALLATION_GUIDE.md)
- **Test Failures**: See [Testing Manual](docs/testing/TESTING_MANUAL.md)
- **Deployment Issues**: See [Deployment Guide](docs/setup/DEPLOYMENT_GUIDE.md)

### Getting Help
1. Check the [Documentation Index](docs/DOCUMENTATION_INDEX.md)
2. Review relevant troubleshooting guides
3. Check test output for specific error messages
4. Consult security documentation for security-related issues

## 📝 License

Copyright (c) 2025 Nguyen, Phuong Duy Lam. All rights reserved.

## 🏆 Acknowledgments

- **Django REST Framework** for robust API development
- **Flutter** for cross-platform mobile development  
- **JWT Authentication** for secure token-based auth
- **pytest** for comprehensive testing framework

---

**Aristay Property Management System** - Professional, Secure, Scalable
*Last Updated: November 23, 2025 - Chat fixes and project reorganization*
