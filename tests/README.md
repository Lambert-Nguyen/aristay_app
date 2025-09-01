# Test Directory

This directory contains all test files organized by functionality.

## Directory Structure

- **`permissions/`** - Tests for dynamic permission system
  - Manager portal tests
  - Dynamic permission changes
  - Permission access validation

- **`api/`** - API endpoint tests
  - API authentication tests
  - ViewSet functionality tests
  - General API behavior tests

- **`booking/`** - Booking system tests
  - Booking conflict tests
  - Booking creation tests
  - Excel import tests
  - Nights handling tests

## Running Tests

To run specific test categories:

```bash
# Run all tests
python -m pytest tests/

# Run permission tests
python -m pytest tests/permissions/

# Run API tests
python -m pytest tests/api/

# Run booking tests
python -m pytest tests/booking/
```

## Test Types

- **Unit Tests**: Individual component testing
- **Integration Tests**: Testing component interactions
- **Permission Tests**: Dynamic permission system validation
- **API Tests**: Endpoint functionality and authentication

## Adding New Tests

1. Place permission-related tests in `permissions/`
2. Place API endpoint tests in `api/`
3. Place booking/business logic tests in `booking/`
4. Follow naming convention: `test_<functionality>.py`
