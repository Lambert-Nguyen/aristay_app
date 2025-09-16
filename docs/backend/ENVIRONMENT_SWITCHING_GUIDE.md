# Environment Switching Guide

## 🎯 **Overview**

The Aristay project uses a simple environment parameter system that allows you to switch between development, testing, and production configurations with a single command. This system integrates with your existing `.env` file structure and requires minimal changes to your workflow.

## 🔧 **How It Works**

### **Environment Detection Flow**
1. **Load .env file** - The system loads your `.env` file first
2. **Read DJANGO_ENVIRONMENT** - Checks the `DJANGO_ENVIRONMENT` parameter
3. **Load appropriate settings** - Based on the value, loads the correct settings file:
   - `development` → `settings_local.py` (uses your .env variables)
   - `testing` → `settings_test.py` (optimized for tests)
   - `production` → `settings_production.py` (production-ready)

### **Settings Files**
- **`settings.py`** - Main settings file with environment detection logic
- **`settings_local.py`** - Development settings (uses your existing .env structure)
- **`settings_test.py`** - Testing settings (in-memory SQLite, fast tests)
- **`settings_production.py`** - Production settings (environment variable driven)

## 🚀 **Quick Start**

### **1. Check Current Environment**
```bash
# From project root
python scripts/add_env_parameter.py --show
```

### **2. Switch Environments**
```bash
# Development (local development)
python scripts/add_env_parameter.py development

# Testing (run tests)
python scripts/add_env_parameter.py testing

# Production (deployment)
python scripts/add_env_parameter.py production
```

### **3. Run Your Application**
```bash
# Activate virtual environment
source .venv/bin/activate

# Start development server
cd aristay_backend && python manage.py runserver

# Run tests
python -m pytest

# Check settings
cd aristay_backend && python manage.py check
```

## 📋 **Environment Configurations**

### **Development Environment**
- **Database**: PostgreSQL (local)
- **Debug**: `True`
- **Email**: Console backend
- **CORS**: Allows all origins
- **Cloudinary**: Uses your existing configuration
- **Settings**: Uses your existing `.env` variables

### **Testing Environment**
- **Database**: In-memory SQLite (fast)
- **Debug**: `True`
- **Email**: LocMem backend
- **CORS**: Allows all origins
- **Cloudinary**: Disabled
- **Settings**: Optimized for speed

### **Production Environment**
- **Database**: PostgreSQL (from `DATABASE_URL`)
- **Debug**: `False`
- **Email**: SMTP backend
- **CORS**: Restricted to allowed origins
- **Cloudinary**: Uses your existing configuration
- **Settings**: Security hardened

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. "No support for ''" Database Error**
**Problem**: Empty `DATABASE_URL` in production mode
**Solution**: Set a valid `DATABASE_URL` in your `.env` file
```bash
# Add to your .env file
DATABASE_URL=postgresql://user:password@host:port/database
```

#### **2. Settings Not Switching**
**Problem**: `DJANGO_SETTINGS_MODULE` environment variable is set
**Solution**: Unset the environment variable
```bash
unset DJANGO_SETTINGS_MODULE
python manage.py check
```

#### **3. Tests Using Wrong Settings**
**Problem**: Tests using development settings instead of test settings
**Solution**: Ensure `pytest.ini` is configured correctly
```ini
[pytest]
DJANGO_SETTINGS_MODULE = backend.settings_test
```

### **Verification Commands**

#### **Check Current Environment**
```bash
# Check .env file
grep DJANGO_ENVIRONMENT aristay_backend/.env

# Check Django settings
cd aristay_backend && python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env', override=True)
print('DJANGO_ENVIRONMENT:', os.getenv('DJANGO_ENVIRONMENT'))
"
```

#### **Verify Settings Loading**
```bash
# Check which settings file is being used
cd aristay_backend && python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()
from django.conf import settings
print('Settings module:', settings.SETTINGS_MODULE)
print('DJANGO_ENVIRONMENT:', getattr(settings, 'DJANGO_ENVIRONMENT', 'NOT_SET'))
"
```

## 📁 **File Structure**

```
aristay_backend/
├── .env                     # Your environment configuration
├── backend/
│   ├── settings.py          # Main settings (environment detection)
│   ├── settings_local.py    # Development settings
│   ├── settings_test.py     # Testing settings
│   ├── settings_production.py # Production settings
│   └── env.example          # Example configuration

scripts/
└── add_env_parameter.py     # Environment switching script

docs/backend/
├── ENVIRONMENT_SWITCHING_GUIDE.md    # This guide
├── ENVIRONMENT_CONFIGURATION.md      # Detailed configuration
└── QUICK_START_ENVIRONMENT.md        # Quick reference
```

## 🎯 **Best Practices**

### **Development Workflow**
1. **Start with development**: `python scripts/add_env_parameter.py development`
2. **Run your app**: `cd aristay_backend && python manage.py runserver`
3. **Make changes**: Edit code, test locally
4. **Run tests**: `python scripts/add_env_parameter.py testing && python -m pytest`
5. **Deploy**: `python scripts/add_env_parameter.py production && git push heroku deployment-clean:main`

### **Testing Workflow**
1. **Switch to testing**: `python scripts/add_env_parameter.py testing`
2. **Run tests**: `python -m pytest`
3. **Check specific tests**: `python -m pytest tests/unit/test_specific.py -v`

### **Production Workflow**
1. **Switch to production**: `python scripts/add_env_parameter.py production`
2. **Verify settings**: `cd aristay_backend && python manage.py check`
3. **Deploy**: `git push heroku deployment-clean:main`

## 🔧 **Advanced Usage**

### **Manual Environment Variable Override**
```bash
# Temporarily override without changing .env
DJANGO_ENVIRONMENT=testing python manage.py check
DJANGO_ENVIRONMENT=production python -m pytest
```

### **Custom Environment Variables**
You can add custom environment variables to your `.env` file:
```bash
# Add to your .env file
CUSTOM_SETTING=value
ANOTHER_SETTING=another_value
```

Then use them in your settings files:
```python
# In settings_local.py, settings_test.py, or settings_production.py
CUSTOM_SETTING = os.getenv('CUSTOM_SETTING', 'default_value')
```

### **Environment-Specific Overrides**
Each settings file can override base settings:
```python
# In settings_local.py
DEBUG = True
SECURE_SSL_REDIRECT = False

# In settings_production.py
DEBUG = False
SECURE_SSL_REDIRECT = True
```

## 📊 **Environment Comparison**

| Setting | Development | Testing | Production |
|---------|-------------|---------|------------|
| Database | PostgreSQL (local) | SQLite (in-memory) | PostgreSQL (DATABASE_URL) |
| Debug | True | True | False |
| Email | Console | LocMem | SMTP |
| CORS | Allow all | Allow all | Restricted |
| Cloudinary | Enabled | Disabled | Enabled |
| SSL Redirect | False | False | True |
| Cache | LocMem | Dummy | Redis (if configured) |

## 🚨 **Important Notes**

1. **Always unset DJANGO_SETTINGS_MODULE** if you have it set in your shell environment
2. **Production requires DATABASE_URL** - set it in your `.env` file
3. **Tests use in-memory SQLite** - no database setup required
4. **Your existing .env variables are preserved** - only `DJANGO_ENVIRONMENT` is added
5. **Environment switching is immediate** - no server restart required for most changes

## 🎉 **Success Indicators**

When everything is working correctly, you should see:
- **Development**: `🔧 Using local development settings with PostgreSQL`
- **Testing**: `🧪 Using test environment settings with in-memory SQLite`
- **Production**: `🚀 Using production settings with environment variables`

The environment switching system is now fully functional and ready for use! 🎉
