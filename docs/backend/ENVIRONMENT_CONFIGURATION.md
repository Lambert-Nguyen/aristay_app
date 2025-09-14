# Environment Configuration Guide

## 🎯 **Overview**

This project uses environment-based Django settings to handle different deployment scenarios while maintaining clean separation between development, testing, and production configurations.

## 📁 **Settings Structure**

```
aristay_backend/backend/
├── settings.py              # Main settings (environment-aware)
├── settings_base.py         # Common settings shared across environments
├── settings_local.py        # Local development settings
├── settings_production.py   # Production deployment settings
├── settings_test.py         # Test environment settings
└── env.example              # Example environment configuration

scripts/
├── manage_env.py            # Python environment management script
└── set_environment.sh       # Bash environment management script
```

## 🔧 **Environment Detection**

The main `settings.py` automatically detects the environment using the `DJANGO_ENVIRONMENT` environment variable:

- **`development`** (default): Uses `settings_local.py`
- **`testing`**: Uses `settings_test.py`  
- **`production`**: Uses `settings_production.py`

## 🚀 **Usage Examples**

### **Simple Environment Switching**

#### **Using the Environment Parameter Script (Recommended)**
```bash
# Switch to development environment
python scripts/add_env_parameter.py development

# Switch to testing environment  
python scripts/add_env_parameter.py testing

# Switch to production environment
python scripts/add_env_parameter.py production

# Show current environment
python scripts/add_env_parameter.py --show
```

#### **Manual .env File Editing**
```bash
# Edit your .env file and change the DJANGO_ENVIRONMENT parameter
DJANGO_ENVIRONMENT=development  # or testing, production
```

#### **Manual Environment Variable Override**
```bash
# Development (default)
python manage.py runserver

# Testing
DJANGO_ENVIRONMENT=testing python -m pytest

# Production
DJANGO_ENVIRONMENT=production python manage.py runserver
```

## ⚙️ **Environment Variables**

### **Development (.env file)**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aristay_local

# Security
SECRET_KEY=local-dev-secret-key-change-me
JWT_SIGNING_KEY=local-jwt-key-change-me

# Environment
DJANGO_ENVIRONMENT=development
DEBUG=true
```

### **Production (Heroku/Environment)**
```bash
# Database (Heroku provides this)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Security (MUST be set)
SECRET_KEY=your-production-secret-key
JWT_SIGNING_KEY=your-production-jwt-key

# Environment
DJANGO_ENVIRONMENT=production
DEBUG=false

# Hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/1

# Optional: Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Optional: Sentry for error tracking
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## 🧪 **Testing Configuration**

The test environment (`settings_test.py`) is optimized for speed and reliability:

- **Database**: In-memory SQLite (fastest)
- **Migrations**: Disabled (faster test startup)
- **Password Hashing**: MD5 (faster than bcrypt)
- **Logging**: Disabled (cleaner output)
- **Cache**: Dummy cache (no external dependencies)
- **Email**: In-memory backend (no actual sending)

## 🔄 **Migration Strategy**

### **From Current Setup**

1. **Backup your current settings**:
   ```bash
   cp aristay_backend/backend/settings.py aristay_backend/backend/settings_backup.py
   ```

2. **Update your .env file**:
   ```bash
   echo "DJANGO_ENVIRONMENT=development" >> .env
   ```

3. **Test the new configuration**:
   ```bash
   # Test development
   python manage.py check
   
   # Test testing
   DJANGO_ENVIRONMENT=testing python manage.py check
   ```

### **Deployment Branch Strategy**

For your `deployment-clean` branch:

1. **Keep production settings in the branch**:
   - `settings_production.py` contains all production configurations
   - Environment variables handle the differences

2. **Local development remains unchanged**:
   - Still uses `settings_local.py`
   - No need to change your local workflow

3. **CI/CD uses test settings**:
   - Tests run with `settings_test.py`
   - Fast, reliable, isolated

## 🛠️ **Development Workflow**

### **Daily Development**
```bash
# Start development server (uses settings_local.py)
python manage.py runserver

# Run tests (uses settings_test.py)
python -m pytest

# Run specific test categories
python -m pytest tests/security/
python -m pytest tests/api/
```

### **Before Deployment**
```bash
# Test with production settings locally
DJANGO_ENVIRONMENT=production python manage.py check

# Run full test suite
python -m pytest
```

### **Deployment**
```bash
# Set production environment
export DJANGO_ENVIRONMENT=production

# Deploy (Heroku will use production settings)
git push heroku deployment-clean:main
```

## 🔍 **Troubleshooting**

### **Settings Not Loading**
```bash
# Check which settings are being used
python manage.py diffsettings | grep DJANGO_ENVIRONMENT

# Verify environment variable
echo $DJANGO_ENVIRONMENT
```

### **Test Failures**
```bash
# Run with verbose output
python -m pytest -v

# Check test settings
DJANGO_ENVIRONMENT=testing python manage.py check
```

### **Production Issues**
```bash
# Check production settings
DJANGO_ENVIRONMENT=production python manage.py check

# Verify environment variables
heroku config --app your-app-name
```

## 📋 **Best Practices**

1. **Never commit secrets**: Use environment variables for all sensitive data
2. **Test all environments**: Run tests with both development and test settings
3. **Document changes**: Update this guide when adding new settings
4. **Use .env for local**: Keep local development configuration in .env file
5. **Validate production**: Always test production settings before deployment

## 🎯 **Benefits**

- **Clean separation**: Each environment has its own configuration
- **Easy testing**: Test environment is optimized for speed
- **Secure production**: Production settings enforce security best practices
- **Flexible development**: Local development remains simple and fast
- **CI/CD friendly**: Tests run in isolated, fast environment
- **Deployment ready**: Production settings handle all deployment scenarios
