# AriStay Backend Testing Documentation

## Overview

This document provides comprehensive information about the automated testing setup for the AriStay Backend application, including local testing, GitHub Actions CI/CD, and test organization.

## 🏗️ Test Structure

```
aristay_backend/
├── tests/                          # Main test directory
│   ├── __init__.py                 # Test package initialization
│   ├── base.py                     # Base test classes and utilities
│   ├── test_models.py              # Model layer tests
│   ├── test_api_views.py           # API endpoint tests
│   ├── test_permissions.py         # Permission and authentication tests
│   ├── test_services.py            # Service layer tests (Excel import, etc.)
│   └── test_integration.py         # Integration and workflow tests
├── backend/
│   └── test_settings.py            # Test-specific Django settings
├── run_tests.py                    # Comprehensive test runner script
├── pytest.ini                     # Pytest configuration
└── .github/workflows/
    └── backend-tests.yml           # GitHub Actions CI/CD workflow
```

## 🚀 Quick Start

### 1. Local Testing

```bash
# Navigate to backend directory
cd aristay_backend

# Install dependencies
pip install -r requirements.txt
pip install coverage pytest-django pytest-cov

# Run all tests
python run_tests.py

# Run specific test suites
python manage.py test tests.test_models
python manage.py test tests.test_api_views
python manage.py test tests.test_permissions
python manage.py test tests.test_services
python manage.py test tests.test_integration

# Run with coverage
coverage run --source='.' manage.py test tests/
coverage report
coverage html  # Generates HTML coverage report
```

### 2. Using pytest (Alternative)

```bash
# Run all tests with pytest
pytest

# Run specific test files
pytest tests/test_models.py
pytest tests/test_api_views.py

# Run with coverage
pytest --cov=api --cov-report=html
```

### 3. GitHub Actions (Automatic)

Tests run automatically on:
- Push to `main`, `develop`, `staging` branches
- Pull requests to `main`, `develop` branches
- Changes to backend code or workflow files

## 📋 Test Categories

### 1. Model Tests (`test_models.py`)
- **Purpose**: Test Django model functionality, validation, and relationships
- **Coverage**:
  - Property model creation and validation
  - Profile model and user roles
  - Task model status and relationships
  - Booking model date validation
  - PropertyOwnership permissions
  - Device and Notification models

**Example**:
```python
def test_property_creation(self):
    """Test creating a property"""
    property_count = Property.objects.count()
    Property.objects.create(name='New Test Property')
    self.assertEqual(Property.objects.count(), property_count + 1)
```

### 2. API View Tests (`test_api_views.py`)
- **Purpose**: Test REST API endpoints, authentication, and responses
- **Coverage**:
  - User registration and authentication
  - Task CRUD operations
  - Property management APIs
  - Booking management APIs
  - Admin user management
  - Notification APIs

**Example**:
```python
def test_task_create_authenticated(self):
    """Test creating a task with authentication"""
    self.authenticate_user('admin')
    url = reverse('task-list')
    data = {
        'property': self.property1.id,
        'title': 'New Test Task',
        'task_type': 'maintenance'
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

### 3. Permission Tests (`test_permissions.py`)
- **Purpose**: Test role-based access control and security
- **Coverage**:
  - Custom permission classes
  - Token authentication
  - Role hierarchy enforcement
  - Property ownership permissions
  - API security measures

**Example**:
```python
def test_staff_cannot_modify_unassigned_tasks(self):
    """Test that staff cannot modify tasks not assigned to them"""
    # Test implementation
```

### 4. Service Tests (`test_services.py`)
- **Purpose**: Test business logic and service layer functionality
- **Coverage**:
  - Excel import service functionality
  - Conflict resolution in imports
  - File handling and validation
  - Error handling and edge cases

**Example**:
```python
def test_basic_excel_import_success(self):
    """Test successful Excel import with valid data"""
    # Test implementation with mock Excel file
```

### 5. Integration Tests (`test_integration.py`)
- **Purpose**: Test complete workflows and system interactions
- **Coverage**:
  - Booking-to-task workflows
  - User role workflows
  - Data consistency checks
  - Full system scenarios

**Example**:
```python
def test_complete_guest_stay_lifecycle(self):
    """Test complete guest stay lifecycle from booking to checkout"""
    # Test end-to-end workflow
```

## 🔧 Configuration

### Environment Variables for Testing

```bash
# Required for local testing
export DJANGO_SETTINGS_MODULE=backend.test_settings
export SECRET_KEY=test-secret-key
export DEBUG=True

# For PostgreSQL testing (optional)
export DATABASE_URL=postgres://user:password@localhost:5432/test_db
```

### Test Settings (`backend/test_settings.py`)

The test settings file optimizes Django for testing:
- Uses in-memory SQLite for speed (or PostgreSQL in CI)
- Disables logging to reduce noise
- Uses fast password hashing
- Disables migrations for speed
- Sets up test-specific middleware

### GitHub Actions Configuration

The CI/CD pipeline (`.github/workflows/backend-tests.yml`) includes:
- **Multi-Python Testing**: Tests against Python 3.9, 3.10, 3.11
- **PostgreSQL Service**: Full database testing
- **Security Checks**: Django deployment checks
- **Code Quality**: Linting with flake8
- **Coverage Reporting**: Codecov integration
- **Artifact Storage**: Test results and coverage reports

## 📊 Coverage Requirements

- **Minimum Coverage**: 80%
- **Coverage Reports**: HTML, XML, and terminal output
- **Coverage Areas**:
  - Models: 95%+ target
  - Views: 90%+ target
  - Services: 85%+ target
  - Utilities: 80%+ target

## 🔍 Test Development Guidelines

### 1. Writing Test Cases

```python
from tests.base import BaseTestCase, BaseAPITestCase

class MyModelTest(BaseTestCase):
    """Test MyModel functionality"""
    
    def setUp(self):
        super().setUp()
        # Additional setup for this test class
    
    def test_model_creation(self):
        """Test creating a model instance"""
        # Test implementation
        self.assertEqual(expected, actual)
```

### 2. API Testing Patterns

```python
class MyAPITest(BaseAPITestCase):
    """Test MyAPI endpoints"""
    
    def test_api_endpoint(self):
        """Test API endpoint"""
        self.authenticate_user('admin')  # Use helper method
        url = reverse('my-endpoint')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
```

### 3. Test Data Management

- Use `setUp()` methods for common test data
- Leverage base classes for shared functionality
- Create factory methods for complex objects
- Clean up test data automatically with Django's TestCase

### 4. Naming Conventions

- Test files: `test_*.py`
- Test classes: `*Test`
- Test methods: `test_*`
- Descriptive names: `test_user_can_create_booking_when_authenticated`

## 🐛 Debugging Tests

### 1. Running Individual Tests

```bash
# Single test method
python manage.py test tests.test_models.PropertyModelTest.test_property_creation

# Single test class
python manage.py test tests.test_models.PropertyModelTest

# With verbose output
python manage.py test tests.test_models --verbosity=2
```

### 2. Test Database Inspection

```bash
# Keep test database for inspection
python manage.py test tests.test_models --keepdb

# Use Django shell with test settings
DJANGO_SETTINGS_MODULE=backend.test_settings python manage.py shell
```

### 3. Coverage Analysis

```bash
# Generate detailed coverage report
coverage run --source='.' manage.py test tests/
coverage report --show-missing
coverage html
# Open coverage_html/index.html in browser
```

## 🔄 Continuous Integration

### GitHub Actions Workflow

1. **Triggers**: Push to main branches, PRs
2. **Matrix Testing**: Multiple Python versions
3. **Database Setup**: PostgreSQL service
4. **Security Checks**: Django deployment validation
5. **Test Execution**: All test suites
6. **Coverage Reporting**: Codecov integration
7. **Artifact Collection**: Reports and logs

### Local CI Simulation

```bash
# Simulate GitHub Actions locally
cd aristay_backend

# Install dependencies
pip install -r requirements.txt
pip install coverage pytest-django pytest-cov flake8

# Run the full test suite like CI
python run_tests.py

# Check deployment readiness
python manage.py check --deploy

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## 📈 Performance Considerations

### 1. Test Speed Optimization

- **In-memory database**: SQLite `:memory:` for unit tests
- **Disabled migrations**: Faster test database setup
- **Minimal logging**: Reduced I/O overhead
- **Test parallelization**: Use `--parallel` flag

### 2. Large Test Suites

```bash
# Run tests in parallel
python manage.py test tests/ --parallel

# Run only fast tests
pytest -m "not slow"

# Run specific test categories
pytest -m "unit"  # Only unit tests
pytest -m "api"   # Only API tests
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure DJANGO_SETTINGS_MODULE is set
   export DJANGO_SETTINGS_MODULE=backend.test_settings
   ```

2. **Database Errors**
   ```bash
   # Reset test database
   python manage.py flush --settings=backend.test_settings
   ```

3. **Permission Errors**
   ```bash
   # Check file permissions
   chmod +x run_tests.py
   ```

4. **Coverage Issues**
   ```bash
   # Clear coverage data
   coverage erase
   coverage run --source='.' manage.py test tests/
   ```

### GitHub Actions Failures

1. **Check logs** in the Actions tab
2. **Review test artifacts** for detailed reports
3. **Local reproduction** using the same commands
4. **Database connectivity** issues in PostgreSQL service

## 📝 Adding New Tests

### 1. Create Test File

```python
# tests/test_new_feature.py
from tests.base import BaseTestCase

class NewFeatureTest(BaseTestCase):
    """Test new feature functionality"""
    
    def test_new_feature(self):
        """Test new feature works correctly"""
        # Implementation
        pass
```

### 2. Update Test Runner

Add new test suite to `run_tests.py`:

```python
{
    'command': 'python manage.py test tests.test_new_feature --verbosity=2',
    'description': 'New Feature Tests',
    'critical': True
}
```

### 3. Update GitHub Actions

Tests automatically run if they're in the `tests/` directory and follow naming conventions.

## 🎯 Test Strategy

### 1. Test Pyramid

- **Unit Tests (70%)**: Models, utilities, individual functions
- **Integration Tests (20%)**: API endpoints, service interactions
- **End-to-End Tests (10%)**: Complete workflows

### 2. Critical Test Areas

1. **Authentication & Authorization**
2. **Data integrity and validation**
3. **API endpoint functionality**
4. **Business logic in services**
5. **Error handling and edge cases**

### 3. Test Maintenance

- **Regular review** of test coverage reports
- **Update tests** when adding new features
- **Refactor tests** to maintain clarity
- **Remove obsolete tests** for deprecated features

## 📞 Support

For questions about the testing setup:

1. **Check this documentation** first
2. **Review test failures** in GitHub Actions
3. **Examine existing tests** for patterns
4. **Run tests locally** to reproduce issues

---

**Happy Testing! 🎉**

This comprehensive test suite ensures the reliability and maintainability of the AriStay Backend application.
