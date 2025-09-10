# Local Development Setup Guide

**Date**: 2025-01-09  
**Version**: 1.0  
**Status**: Complete

## Overview

This guide explains how to set up local development environment that mirrors the Heroku production environment, ensuring consistency between local development and production deployment.

## Prerequisites

- Python 3.13+
- PostgreSQL 14+
- Virtual environment activated
- Git repository cloned

## Quick Start

### 1. Initial Setup (One-time)

```bash
# Run the setup script
./scripts/development/setup_local_dev.sh
```

### 2. Start Development Server

```bash
# Start local development server
./scripts/development/dev_local.sh
```

### 3. Access Your Application

- **Backend API**: http://127.0.0.1:8000
- **Admin Interface**: http://127.0.0.1:8000/admin
- **API Documentation**: http://127.0.0.1:8000/api/schema/swagger-ui/

## Architecture

### Database Configuration

**Local Development**:
- **Database**: PostgreSQL (`aristay_local`)
- **Host**: 127.0.0.1:5432
- **User**: postgres
- **Settings**: Default `backend.settings` (no custom settings module needed)

**Production (Heroku)**:
- **Database**: PostgreSQL (Heroku Postgres)
- **Host**: Heroku managed
- **Settings**: `backend.settings`

### Key Differences from Production

| Setting | Local Development | Production |
|---------|------------------|------------|
| Database | PostgreSQL (local) | PostgreSQL (Heroku) |
| Debug Mode | `True` | `False` |
| Secret Key | Local development key | Production key |
| SSL Redirect | `False` | `True` |
| Email Backend | Console | SMTP |
| CORS Origins | Localhost URLs | Production URLs |

## Scripts Reference

### `setup_local_dev.sh`
**Purpose**: One-time setup for local development environment

**What it does**:
1. Installs PostgreSQL (if not present)
2. Creates `aristay_local` database
3. Runs Django migrations
4. Sets up local development configuration

**Usage**:
```bash
./scripts/development/setup_local_dev.sh
```

### `dev_local.sh`
**Purpose**: Start local development server with PostgreSQL

**What it does**:
1. Activates virtual environment
2. Exports PostgreSQL env vars (`POSTGRES_*`) if not set
3. Runs migrations
4. Starts Django development server using default settings

**Usage**:
```bash
./scripts/development/dev_local.sh
```

### `deploy.sh`
**Purpose**: Deploy to Heroku from deployment branch

**What it does**:
1. Switches to `deployment-clean` branch
2. Pushes to Heroku main branch
3. Triggers Heroku deployment

**Usage**:
```bash
./scripts/deployment/deploy.sh
```

## Development Workflow

### 1. Daily Development

```bash
# Start your day
./scripts/development/dev_local.sh

# Make your changes
# Test locally at http://127.0.0.1:8000

# When ready to deploy
./scripts/deployment/deploy.sh
```

### 2. Database Management

```bash
# Run migrations
cd aristay_backend
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load test data
python manage.py seed_test_data
```

### 3. Testing

```bash
# Run tests
cd aristay_backend
python manage.py test

# Run specific test categories
python ../tests/run_tests.py --security
python ../tests/run_tests.py --api
```

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Error
```
FATAL: role "postgres" does not exist
```

**Solution**:
```bash
createuser -s postgres
```

#### 2. Database Already Exists
```
Database aristay_local already exists
```

**Solution**: This is normal - the script handles this gracefully.

#### 3. Migration Errors
```
sqlite3.OperationalError: near "EXTENSION": syntax error
```

**Solution**: Make sure you're using the local settings:
```bash
python manage.py migrate --settings=backend.settings_local
```

#### 4. Port Already in Use
```
Error: That port is already in use
```

**Solution**: Kill existing processes or use a different port:
```bash
lsof -ti:8000 | xargs kill -9
```

### Environment Variables

The local development setup uses these environment variables:

```bash
# Either DATABASE_URL or POSTGRES_* can be used
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/aristay_local
POSTGRES_DB=aristay_local
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

DEBUG=true
DJANGO_ENVIRONMENT=development
SECRET_KEY=local-dev-secret-key-change-me
JWT_SIGNING_KEY=local-jwt-key-change-me
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## File Structure

```
aristay_app/
├── scripts/
│   ├── development/
│   │   ├── setup_local_dev.sh      # Initial setup
│   │   └── dev_local.sh            # Start dev server
│   └── deployment/
│       └── deploy.sh               # Deploy to Heroku
├── aristay_backend/
│   ├── backend/
│   │   └── settings.py             # Unified settings (local/prod via env)
│   └── manage.py
└── docs/
    └── development/
        └── LOCAL_DEVELOPMENT_SETUP.md  # This file
```

## Best Practices

1. **Use default settings with env vars** (no custom module needed).

2. **Test locally before deploying**:
   - Run the development server
   - Test all functionality
   - Run tests
   - Deploy only when everything works

3. **Keep databases in sync**:
   - Local PostgreSQL mirrors Heroku PostgreSQL
   - Same migrations, same constraints
   - No SQLite compatibility issues

4. **Use version control properly**:
   - Develop on `main` branch
   - Deploy from `deployment-clean` branch
   - Never commit directly to deployment branch

## Security Notes

- Local development uses different secret keys
- No production data in local environment
- Console email backend for testing
- Debug mode enabled for development

## Support

If you encounter issues:

1. Check this documentation
2. Review the troubleshooting section
3. Check the logs in `aristay_backend/logs/`
4. Verify PostgreSQL is running: `brew services list | grep postgresql`

---

**Last Updated**: 2025-01-09  
**Maintained By**: Development Team  
**Next Review**: 2025-02-09
