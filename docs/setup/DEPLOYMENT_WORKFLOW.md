# Deployment Workflow Documentation

**Date**: 2025-01-09  
**Version**: 1.0  
**Status**: Complete

## Overview

This document describes the complete deployment workflow for the Aristay Property Management system, including local development, staging, and production deployment processes.

## Architecture Overview

### Branch Strategy

```
GitHub Repository:
├── main                    # Clean development branch
├── deployment-clean        # Deployment branch with Heroku files
└── feature/*              # Feature branches

Heroku Repository:
└── main                   # Deployment environment
```

### Deployment Flow

```
Local Development → GitHub main → deployment-clean → Heroku main
```

## Prerequisites

- Git repository access
- Heroku CLI installed and authenticated
- PostgreSQL installed locally
- Virtual environment set up

## Scripts Reference

### Development Scripts

#### `scripts/development/setup_local_dev.sh`
**Purpose**: Initial local development environment setup

**Features**:
- Installs PostgreSQL if needed
- Creates local database (`aristay_local`)
- Runs Django migrations
- Sets up local development configuration

**Usage**:
```bash
./scripts/development/setup_local_dev.sh
```

**Output**:
- PostgreSQL database created
- Django migrations applied
- Local development environment ready

#### `scripts/development/dev_local.sh`
**Purpose**: Start local development server

**Features**:
- Activates virtual environment
- Uses local PostgreSQL settings
- Starts Django development server
- Enables debug mode

**Usage**:
```bash
./scripts/development/dev_local.sh
```

**Output**:
- Development server running on http://127.0.0.1:8000
- Console email backend active
- Debug mode enabled

### Deployment Scripts

#### `scripts/deployment/deploy.sh`
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

**Output**:
- Code pushed to Heroku
- Heroku deployment triggered
- Application URL provided

## Complete Workflow

### 1. Initial Setup (One-time)

```bash
# Clone repository
git clone <repository-url>
cd aristay_app

# Set up local development
./scripts/development/setup_local_dev.sh

# Verify setup
./scripts/development/dev_local.sh
```

### 2. Daily Development Workflow

```bash
# 1. Start development
git checkout main
./scripts/development/dev_local.sh

# 2. Make changes
# Edit code, test locally

# 3. Commit changes
git add .
git commit -m "Your changes"
git push origin main

# 4. Deploy when ready
./scripts/deployment/deploy.sh
```

### 3. Feature Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature
git push origin feature/your-feature

# 2. Develop locally
./scripts/development/dev_local.sh
# Make changes, test

# 3. Merge to main
git checkout main
git merge feature/your-feature
git push origin main

# 4. Deploy
./scripts/deployment/deploy.sh
```

## Environment Configuration

### Local Development Environment

**Database**: PostgreSQL (`aristay_local`)  
**Settings**: `backend.settings_local`  
**Debug**: `True`  
**Email**: Console backend  

**Key Files**:
- `aristay_backend/backend/settings_local.py`
- `scripts/development/dev_local.sh`
- `scripts/development/setup_local_dev.sh`

### Production Environment (Heroku)

**Database**: Heroku Postgres  
**Settings**: `backend.settings`  
**Debug**: `False`  
**Email**: SMTP backend  

**Key Files**:
- `Procfile` (root level)
- `requirements.txt` (root level)
- `runtime.txt` (root level)

## Branch Management

### Main Branch (`main`)
- **Purpose**: Clean development branch
- **Contains**: Source code only
- **Excludes**: Heroku deployment files
- **Workflow**: Feature development, testing

### Deployment Branch (`deployment-clean`)
- **Purpose**: Deployment-ready branch
- **Contains**: Source code + Heroku files
- **Includes**: `Procfile`, `requirements.txt`, `runtime.txt`
- **Workflow**: Deployment to Heroku

### Heroku Branch (`main`)
- **Purpose**: Heroku deployment environment
- **Contains**: Complete deployment package
- **Source**: `deployment-clean` branch
- **Workflow**: Automatic deployment

## File Organization

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
│   │   ├── settings.py             # Production settings
│   │   └── settings_local.py       # Local development settings
│   └── manage.py
├── Procfile                        # Heroku process file
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version
└── docs/
    ├── development/
    │   └── LOCAL_DEVELOPMENT_SETUP.md
    └── setup/
        └── DEPLOYMENT_WORKFLOW.md  # This file
```

## Deployment Process Details

### 1. Code Preparation

```bash
# Ensure you're on main branch
git checkout main

# Pull latest changes
git pull origin main

# Verify changes
git status
```

### 2. Deployment Execution

```bash
# Run deployment script
./scripts/deployment/deploy.sh
```

**What happens**:
1. Switches to `deployment-clean` branch
2. Pushes to Heroku main branch
3. Heroku detects changes and starts build
4. Runs `release` command (migrations)
5. Starts web process

### 3. Post-Deployment Verification

```bash
# Check deployment status
heroku ps -a aristay-internal-backend

# View logs
heroku logs -a aristay-internal-backend

# Test application
curl https://aristay-internal-backend-72ffd16c9352.herokuapp.com/
```

## Troubleshooting

### Common Deployment Issues

#### 1. Build Failures
```bash
# Check build logs
heroku logs -a aristay-internal-backend --tail

# Common causes:
# - Missing dependencies in requirements.txt
# - Python version mismatch
# - Database migration errors
```

#### 2. Migration Failures
```bash
# Run migrations manually
heroku run python manage.py migrate -a aristay-internal-backend

# Check migration status
heroku run python manage.py showmigrations -a aristay-internal-backend
```

#### 3. Application Errors
```bash
# Check application logs
heroku logs -a aristay-internal-backend --tail

# Restart application
heroku restart -a aristay-internal-backend
```

### Local Development Issues

#### 1. Database Connection
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@14
```

#### 2. Migration Errors
```bash
# Use local settings
python manage.py migrate --settings=backend.settings_local

# Reset database (if needed)
dropdb aristay_local
createdb aristay_local
python manage.py migrate --settings=backend.settings_local
```

## Security Considerations

### Local Development
- Uses separate secret keys
- Debug mode enabled
- Console email backend
- Local database only

### Production
- Secure secret keys
- Debug mode disabled
- SMTP email backend
- Heroku-managed database
- SSL enforcement

## Monitoring and Maintenance

### Health Checks
```bash
# Check application status
heroku ps -a aristay-internal-backend

# Monitor logs
heroku logs -a aristay-internal-backend --tail

# Check database
heroku pg:info -a aristay-internal-backend
```

### Regular Maintenance
- Monitor Heroku logs for errors
- Check database performance
- Update dependencies regularly
- Review security settings

## Best Practices

1. **Always test locally before deploying**
2. **Use feature branches for new development**
3. **Keep deployment branch clean and ready**
4. **Monitor deployment logs**
5. **Use environment-specific settings**
6. **Maintain separate databases for local/production**

## Support and Resources

- **Heroku Documentation**: https://devcenter.heroku.com/
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

**Last Updated**: 2025-01-09  
**Maintained By**: Development Team  
**Next Review**: 2025-02-09
