# 🏨 Aristay - Property Management System

**Aristay** is a comprehensive property management platform designed for modern hospitality operations. It features a robust Django REST API backend with JWT authentication, automated task management, and a Flutter mobile application for on-the-go property management.

## 🎯 Project Overview

### Core Features
- 🔐 **JWT Authentication** - Secure, token-based authentication system
- 📋 **Booking Management** - Comprehensive reservation and guest management
- 🤖 **Task Automation** - Automated cleaning and maintenance task creation
- 👥 **Role-Based Access Control** - Granular permission system
- 📱 **Mobile Application** - Flutter-based mobile interface
- 📊 **Admin Dashboard** - Staff management and reporting interface

### Technology Stack
- **Backend**: Django REST Framework with PostgreSQL
- **Frontend**: Flutter mobile application
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
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Official project organization
- **[docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** - Complete documentation guide

### 🔗 Quick Links
- **Setup**: [Installation Guide](docs/setup/INSTALLATION_GUIDE.md) | [Deployment Guide](docs/setup/DEPLOYMENT_GUIDE.md)
- **Security**: [JWT Authentication](docs/features/JWT_AUTHENTICATION.md) | [Security Guide](docs/security/SECURITY_IMPLEMENTATION_COMPLETE.md)
- **Testing**: [Testing Strategy](docs/testing/TESTING_STRATEGY.md) | [System Testing Guide](docs/SYSTEM_TESTING_GUIDE.md)
- **Development**: [API Documentation](docs/development/API_DOCUMENTATION.md) | [Backend Docs](docs/backend/README.md)

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
├── PROJECT_STRUCTURE.md           # Official project organization
├── aristay_backend/               # Django REST API
├── aristay_flutter_frontend/      # Flutter mobile app  
├── tests/                         # Comprehensive test suite
├── docs/                          # Complete documentation
├── scripts/                       # Development & admin scripts
└── tools/                         # Development utilities
```

For the complete structure overview, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## 📊 Project Status

✅ **Production Ready** - All core features implemented and tested  
✅ **Security Hardened** - Comprehensive security implementation  
✅ **Well Documented** - Complete documentation and guides  
✅ **Fully Tested** - Comprehensive test coverage  
✅ **Organized Structure** - Professional project organization  

For detailed status information, see [Final Project Status](docs/reports/FINAL_PROJECT_STATUS.md).

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

This project is proprietary software developed for Aristay property management operations.

## 🏆 Acknowledgments

- **Django REST Framework** for robust API development
- **Flutter** for cross-platform mobile development  
- **JWT Authentication** for secure token-based auth
- **pytest** for comprehensive testing framework

---

**Aristay Property Management System** - Professional, Secure, Scalable  
*Last Updated: Project reorganization completion*
