# Quick Start: Environment Management

## 🚀 **Quick Commands**

### **Switch Environment**
```bash
# Development (default)
python scripts/add_env_parameter.py development

# Testing
python scripts/add_env_parameter.py testing

# Production
python scripts/add_env_parameter.py production
```

### **Run Application**
```bash
# Start development server
cd aristay_backend && python manage.py runserver

# Run tests
python -m pytest

# Check settings
cd aristay_backend && python manage.py check
```

## 📋 **Environment Checklist**

### **Development Setup**
- [ ] Run `python scripts/add_env_parameter.py development`
- [ ] Verify PostgreSQL is running
- [ ] Run `cd aristay_backend && python manage.py check`
- [ ] Start server with `python manage.py runserver`

### **Testing Setup**
- [ ] Run `python scripts/add_env_parameter.py testing`
- [ ] Run `python -m pytest` to verify tests work
- [ ] All tests should pass

### **Production Setup**
- [ ] Run `python scripts/add_env_parameter.py production`
- [ ] Update `.env` file with real production values
- [ ] Set secure `SECRET_KEY` and `JWT_SIGNING_KEY`
- [ ] Configure `DATABASE_URL` for production database
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure email settings if needed

## 🔧 **Troubleshooting**

### **Common Issues**

1. **"No support for ''" error**
   - Solution: Run `python scripts/manage_env.py development`

2. **Tests failing**
   - Solution: Run `python scripts/manage_env.py testing`

3. **Settings not loading**
   - Solution: Check `.env` file exists in `aristay_backend/` directory

4. **Database connection issues**
   - Solution: Verify PostgreSQL is running and credentials are correct

### **Verify Environment**
```bash
# Check current environment
python scripts/add_env_parameter.py --show

# Check Django settings
cd aristay_backend && python manage.py check

# Check which settings file is being used
cd aristay_backend && python -c "from django.conf import settings; print(settings.SETTINGS_MODULE)"
```

## 📁 **File Locations**

- **Environment file**: `aristay_backend/.env`
- **Settings files**: `aristay_backend/backend/settings_*.py`
- **Management scripts**: `scripts/add_env_parameter.py`
- **Example config**: `aristay_backend/backend/env.example`
