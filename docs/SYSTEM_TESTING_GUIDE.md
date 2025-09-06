# 🏗️ System Testing Guide

## Overview
This guide focuses on system-level testing for the Aristay application, covering end-to-end validation, system integration, and production readiness verification.

## System Test Categories

### 1. 🛡️ **Production System Tests**
**Purpose:** Validate production-grade system hardening and integrity

#### Test Execution
```bash
# Primary system test - hermetic and self-contained
cd /path/to/aristay_app
python tests/production/test_production_hardening.py
```

#### System Validations
- **Idempotent Operations:** Ensures system handles repeated operations gracefully
- **Data Integrity:** Verifies database constraints prevent corruption
- **State Consistency:** Confirms unified state management across components

### 2. 🔗 **Integration System Tests** 
**Purpose:** End-to-end system workflow validation

#### Test Execution
```bash
cd aristay_backend
python -m pytest ../tests/integration/ -v --tb=short
```

#### System Scenarios
- **Multi-component workflows**
- **Cross-service communication**
- **Data flow validation**
- **Error handling and recovery**

### 3. 🌐 **Full System Validation**
**Purpose:** Comprehensive system health check

#### Centralized System Runner
```bash
# Runs all system test categories
python tests/run_tests.py
```

#### Manual System Verification
```bash
# Step-by-step system validation
echo "🧪 COMPREHENSIVE SYSTEM TEST"
echo "============================================================"

echo "1. Production Hardening Tests:"
python tests/production/test_production_hardening.py

echo "2. Integration System Tests:"
cd aristay_backend && python -m pytest ../tests/integration/ -v

echo "3. Unit Component Tests:"
python -m pytest ../tests/unit/ -v

echo "✅ System validation complete"
```

## System Test Scenarios

### 🎯 **Critical System Paths**

#### Booking Management System Flow
```bash
# Test the complete booking lifecycle
cd aristay_backend
python -m pytest ../tests/integration/test_final_phases.py::test_all_phases_complete -v
```

#### Task Management System Flow  
```bash
# Test automated task creation and management
python tests/production/test_production_hardening.py
```

#### Permission Management System
```bash
# Test role-based access control system
cd aristay_backend  
python -m pytest ../tests/unit/ -k "permission" -v
```

### 🔄 **System State Management**

#### Database System Tests
```bash
# Test database integrity and constraints
cd aristay_backend
python manage.py check
python manage.py migrate --check
```

#### File System Tests
```bash
# Test file upload and storage systems
cd aristay_backend
python -m pytest ../tests/integration/ -k "file" -v
```

## Production System Validation

### 🚀 **Pre-Deployment System Checks**

#### Complete System Health Check
```bash
#!/bin/bash
# comprehensive_system_test.sh

echo "🏗️ ARISTAY SYSTEM VALIDATION"
echo "============================================================"

# 1. Environment validation
echo "📋 Environment Check:"
python -c "import django; print(f'✅ Django {django.VERSION}')"
python -c "from api.models import Task; print('✅ Models accessible')"

# 2. Database system check
echo "📋 Database System:"
cd aristay_backend
python manage.py check --database default
python manage.py showmigrations

# 3. Production hardening validation
echo "📋 Production Hardening:"
cd ..
python tests/production/test_production_hardening.py

# 4. Integration system tests
echo "📋 Integration Systems:" 
cd aristay_backend
python -m pytest ../tests/integration/ -v --tb=short

# 5. System configuration validation
echo "📋 System Configuration:"
python manage.py check --deploy

echo "✅ System validation complete"
```

#### CI/CD System Validation
```bash
# Simulate CI environment locally
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH="$(pwd)/aristay_backend" 
export DEBUG=0

cd aristay_backend
python -m pytest ../tests/ -v --tb=short
```

### 📊 **System Performance Testing**

#### Load Testing Setup
```bash
# Test system under load (requires additional tools)
cd aristay_backend
python manage.py test --parallel 4
```

#### Memory and Performance Profiling
```bash
# System resource monitoring during tests
cd aristay_backend
python -m pytest ../tests/integration/ --profile-svg
```

## System Monitoring & Logging

### 📝 **System Test Logging**

#### Enable Verbose System Logging
```bash
# Run with comprehensive logging
cd aristay_backend
DJANGO_LOG_LEVEL=DEBUG python -m pytest ../tests/integration/ -v -s
```

#### Monitor System Events
```bash
# Watch system logs during testing
tail -f aristay_backend/logs/debug.log
```

### 🔍 **System Diagnostics**

#### System Health Diagnostics
```bash
cd aristay_backend

# Database connectivity
python manage.py dbshell --command="SELECT 1;"

# Model integrity  
python manage.py check --tag models

# URL routing system
python manage.py show_urls | head -20

# Static files system
python manage.py collectstatic --dry-run
```

#### System Dependencies Check
```bash
# Verify all system dependencies
pip check
python -c "import django, rest_framework, pytest; print('✅ Core dependencies available')"
```

## System Recovery & Resilience Testing

### 🛠️ **System Recovery Tests**

#### Database Recovery Testing
```bash
# Test system recovery from various states
cd aristay_backend

# Backup current state
python manage.py dumpdata --natural-foreign --natural-primary > system_backup.json

# Test recovery
python manage.py flush --noinput
python manage.py loaddata system_backup.json
python tests/production/test_production_hardening.py
```

#### System Rollback Testing
```bash
# Test system rollback capabilities
cd aristay_backend
python manage.py migrate api zero
python manage.py migrate
python -m pytest ../tests/integration/ -v
```

### 🔒 **System Security Testing**

#### Permission System Validation
```bash
cd aristay_backend
python -m pytest ../tests/unit/ -k "permission" -v
python -c "from api.authz import AuthzHelper; print('✅ Authorization system loaded')"
```

#### System Input Validation
```bash
# Test system input sanitization and validation
cd aristay_backend  
python -m pytest ../tests/integration/ -k "validation" -v
```

## System Deployment Testing

### 🌍 **Environment-Specific System Tests**

#### Development System
```bash
export DJANGO_SETTINGS_MODULE=backend.settings
export DEBUG=1
python tests/production/test_production_hardening.py
```

#### Production-Like System
```bash
export DJANGO_SETTINGS_MODULE=backend.settings
export DEBUG=0
export SECRET_KEY="production-test-key"
python tests/production/test_production_hardening.py
```

### 🚀 **Deployment System Validation**

#### Pre-Deployment System Checklist
```bash
#!/bin/bash
echo "🚀 PRE-DEPLOYMENT SYSTEM VALIDATION"
echo "============================================================"

# System integrity
python tests/production/test_production_hardening.py || exit 1

# Integration systems  
cd aristay_backend
python -m pytest ../tests/integration/ -v || exit 1

# Security checks
python manage.py check --deploy || exit 1

# Database migrations
python manage.py migrate --check || exit 1

# Static files system
python manage.py collectstatic --noinput --clear || exit 1

echo "✅ System ready for deployment"
```

#### Post-Deployment System Verification
```bash
# Verify system after deployment
curl -f http://localhost:8000/api/health/ || exit 1
python tests/production/test_production_hardening.py || exit 1
```

## System Testing Best Practices

### 📋 **System Test Guidelines**

1. **Hermetic Testing:** System tests should be self-contained
2. **State Management:** Clean up system state after tests
3. **Resource Cleanup:** Ensure no resource leaks
4. **Error Handling:** Test system failure scenarios
5. **Performance:** Monitor system resource usage

### 🎯 **System Test Success Criteria**

#### Green System Indicators
```
🚀 ALL PRODUCTION HARDENING TESTS PASSED!
✅ Idempotent task creation working
✅ DB constraints preventing duplicates
✅ Status mapping unified and consistent

======================== X passed, 0 warnings ========================
```

#### System Ready Checklist
- [ ] All production system tests passing
- [ ] Integration system workflows validated  
- [ ] Database system integrity confirmed
- [ ] Security system permissions verified
- [ ] Performance system metrics acceptable
- [ ] Deployment system checks successful

---

## 🏁 System Test Summary

The Aristay system testing framework provides comprehensive validation across:

- **Production hardening** with idempotent operations
- **Integration workflows** with end-to-end validation  
- **Database integrity** with constraint enforcement
- **Security systems** with role-based access control
- **Performance systems** with resource monitoring

**System Status:** Ready for production deployment with automated validation pipeline.

---

*For detailed command references, see the main [Testing Manual](TESTING_MANUAL.md).*
