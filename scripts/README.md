# Scripts Documentation

**Date**: 2025-01-09  
**Version**: 1.0  
**Status**: Complete

## Overview

This directory contains all automation scripts for the Aristay Property Management system, organized by functionality and following the project structure guidelines.

## Directory Structure

```
scripts/
├── admin/                    # Administrative scripts
│   ├── audit_user_access.py
│   ├── seed_new_permissions.py
│   └── user_management.py
├── development/              # Local development scripts
│   ├── setup_local_dev.sh   # Initial development setup
│   └── dev_local.sh         # Start development server
├── deployment/               # Deployment scripts
│   └── deploy.sh            # Deploy to Heroku
├── permissions/              # Permission management scripts
│   ├── create_permissions.py
│   ├── sync_permissions.py
│   └── validate_permissions.py
├── testing/                  # Testing automation scripts
│   ├── quick_test.sh
│   ├── jwt_smoke_test_improved.sh
│   └── run_tests.py
└── README.md                # This file
```

## Development Scripts

### `development/setup_local_dev.sh`
**Purpose**: One-time setup for local development environment

**Features**:
- Installs PostgreSQL if needed
- Creates local database (`aristay_local`)
- Runs Django migrations
- Sets up local development configuration

**Usage**:
```bash
./scripts/development/setup_local_dev.sh
```

**Prerequisites**:
- Python 3.13+
- Virtual environment activated
- Git repository cloned

**Output**:
- PostgreSQL database created
- Django migrations applied
- Local development environment ready

### `development/dev_local.sh`
**Purpose**: Start local development server with PostgreSQL

**Features**:
- Activates virtual environment
- Uses local PostgreSQL settings
- Starts Django development server
- Enables debug mode

**Usage**:
```bash
./scripts/development/dev_local.sh
```

**Prerequisites**:
- Local development environment set up
- PostgreSQL running
- Virtual environment activated

**Output**:
- Development server running on http://127.0.0.1:8000
- Console email backend active
- Debug mode enabled

## Deployment Scripts

### `deployment/deploy.sh`
**Purpose**: Deploy to Heroku from deployment branch

**Features**:
- Switches to `deployment-clean` branch
- Pushes to Heroku main branch
- Triggers Heroku deployment
- Provides deployment URL

**Usage**:
```bash
./scripts/deployment/deploy.sh
```

**Prerequisites**:
- Heroku CLI installed and authenticated
- Git repository with deployment branch
- Heroku app configured

**Output**:
- Code pushed to Heroku
- Heroku deployment triggered
- Application URL provided

## Administrative Scripts

### `admin/audit_user_access.py`
**Purpose**: Audit user access and permissions

**Usage**:
```bash
python scripts/admin/audit_user_access.py
```

### `admin/seed_new_permissions.py`
**Purpose**: Seed new permissions into the system

**Usage**:
```bash
python scripts/admin/seed_new_permissions.py
```

## Permission Management Scripts

### `permissions/create_permissions.py`
**Purpose**: Create new permissions programmatically

**Usage**:
```bash
python scripts/permissions/create_permissions.py
```

### `permissions/sync_permissions.py`
**Purpose**: Synchronize permissions across environments

**Usage**:
```bash
python scripts/permissions/sync_permissions.py
```

### `permissions/validate_permissions.py`
**Purpose**: Validate permission configuration

**Usage**:
```bash
python scripts/permissions/validate_permissions.py
```

## Testing Scripts

### `testing/quick_test.sh`
**Purpose**: Run quick test suite

**Usage**:
```bash
./scripts/testing/quick_test.sh
```

### `testing/jwt_smoke_test_improved.sh`
**Purpose**: Test JWT authentication system

**Usage**:
```bash
./scripts/testing/jwt_smoke_test_improved.sh
```

### `testing/run_tests.py`
**Purpose**: Comprehensive test runner

**Usage**:
```bash
python scripts/testing/run_tests.py --security
python scripts/testing/run_tests.py --api
python scripts/testing/run_tests.py --production
```

## Common Workflows

### Initial Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd aristay_app

# 2. Set up local development
./scripts/development/setup_local_dev.sh

# 3. Start development
./scripts/development/dev_local.sh
```

### Daily Development
```bash
# 1. Start development server
./scripts/development/dev_local.sh

# 2. Make changes and test
# Visit http://127.0.0.1:8000

# 3. Deploy when ready
./scripts/deployment/deploy.sh
```

### Testing
```bash
# Run all tests
python scripts/testing/run_tests.py

# Run specific test categories
python scripts/testing/run_tests.py --security
python scripts/testing/run_tests.py --api
```

## Script Requirements

### Shell Scripts
- **Shebang**: `#!/bin/bash`
- **Permissions**: Executable (`chmod +x`)
- **Error Handling**: Exit on error (`set -e`)
- **Logging**: Informative output messages

### Python Scripts
- **Shebang**: `#!/usr/bin/env python3`
- **Imports**: Django settings configured
- **Error Handling**: Try-catch blocks
- **Logging**: Use Django logging system

## Environment Variables

Scripts use these environment variables:

```bash
# Database
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/aristay_local

# Django
DEBUG=true
DJANGO_ENVIRONMENT=development
SECRET_KEY=local-dev-secret-key-change-me
JWT_SIGNING_KEY=local-jwt-key-change-me

# CORS and Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Fix script permissions
chmod +x scripts/development/*.sh
chmod +x scripts/deployment/*.sh
```

#### 2. Virtual Environment Not Found
```bash
# Ensure virtual environment exists
python -m venv .venv
source .venv/bin/activate
```

#### 3. PostgreSQL Connection Error
```bash
# Start PostgreSQL
brew services start postgresql@14

# Create user if needed
createuser -s postgres
```

#### 4. Heroku Authentication Error
```bash
# Login to Heroku
heroku login

# Check authentication
heroku auth:whoami
```

## Best Practices

1. **Always test scripts locally before using in production**
2. **Use descriptive script names and comments**
3. **Include error handling and logging**
4. **Document script purpose and usage**
5. **Keep scripts in appropriate directories**
6. **Use environment variables for configuration**
7. **Make scripts idempotent when possible**

## Security Considerations

- Scripts use local development keys (not production)
- Database connections use local PostgreSQL
- No production secrets in scripts
- Debug mode enabled for development
- Console email backend for testing

## Maintenance

### Regular Tasks
- Review script functionality
- Update documentation
- Test script reliability
- Check for security issues

### Version Control
- All scripts are version controlled
- Changes require pull request review
- Scripts are tested before deployment

---

**Last Updated**: 2025-01-09  
**Maintained By**: Development Team  
**Next Review**: 2025-02-09