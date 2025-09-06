# 🧪 Aristay Testing User Manual

## Overview
This manual provides comprehensive instructions for running all tests in the Aristay booking management system. The test suite is organized into three main categories with different execution methods available.

## Test Structure

```
tests/
├── production/           # Production hardening & system integrity tests
├── integration/         # End-to-end workflow and feature tests  
├── unit/               # Component-level unit tests
└── run_tests.py        # Centralized test runner
```

## Quick Start

### 🚀 **Run All Tests (Recommended)**
```bash
# From project root
cd /path/to/aristay_app
python tests/run_tests.py
```

### ⚡ **Individual Test Categories**
```bash
# Production hardening tests
python tests/production/test_production_hardening.py

# Integration tests  
cd aristay_backend && python -m pytest ../tests/integration/ -v

# Unit tests
cd aristay_backend && python -m pytest ../tests/unit/ -v
```

## Detailed Test Categories

### 1. 🛡️ **Production Tests**
**Purpose:** Validate production-grade hardening and system integrity

**Location:** `tests/production/`

**Key Tests:**
- **Idempotent Task Creation** - Ensures no duplicate automated tasks
- **Database Constraints** - Verifies DB-level uniqueness enforcement
- **Status Mapping Consistency** - Tests unified booking status handling

**Run Commands:**
```bash
# Direct execution (hermetic tests)
python tests/production/test_production_hardening.py

# Via pytest
cd aristay_backend
python -m pytest ../tests/production/ -v --tb=short
```

**Expected Output:**
```
🧪 IDEMPOTENCE TEST: Task Creation
🎉 IDEMPOTENCE TEST PASSED: Second call created no duplicates!

🧪 CONSTRAINT TEST: DB-Level Uniqueness  
🎉 CONSTRAINT TEST PASSED: DB constraint prevented duplicate task!

🧪 STATUS MAPPING TEST: Unified Mapping Consistency
🎉 STATUS MAPPING TEST PASSED: All mappings are consistent!

🚀 ALL PRODUCTION HARDENING TESTS PASSED!
```

### 2. 🔗 **Integration Tests**  
**Purpose:** End-to-end workflow validation and feature integration testing

**Location:** `tests/integration/`

**Key Tests:**
- **Comprehensive System Test** - Full workflow validation
- **Final Phases Test** - Multi-phase integration scenarios
- **Duplicate Prevention** - Cross-component duplicate detection

**Run Commands:**
```bash
# From backend directory
cd aristay_backend
python -m pytest ../tests/integration/ -v

# Specific test file
python -m pytest ../tests/integration/test_final_phases.py -v

# With detailed output
python -m pytest ../tests/integration/ -v --tb=short -s
```

### 3. 🔬 **Unit Tests**
**Purpose:** Component-level testing and isolated functionality validation

**Location:** `tests/unit/`

**Run Commands:**
```bash
# From backend directory  
cd aristay_backend
python -m pytest ../tests/unit/ -v

# With coverage report
python -m pytest ../tests/unit/ --cov=api --cov-report=term-missing

# Specific test patterns
python -m pytest ../tests/unit/ -k "test_booking" -v
```

## Advanced Usage

### 🎯 **Focused Testing**

**Run Specific Test Functions:**
```bash
cd aristay_backend
python -m pytest ../tests/integration/test_final_phases.py::test_all_phases_complete -v
```

**Filter by Test Names:**
```bash
python -m pytest ../tests/ -k "idempotent" -v
python -m pytest ../tests/ -k "not slow" -v
```

**Run with Different Verbosity:**
```bash
python -m pytest ../tests/production/ -v          # Verbose
python -m pytest ../tests/production/ -q          # Quiet  
python -m pytest ../tests/production/ -vv         # Extra verbose
```

### 🔧 **Environment Setup**

**Prerequisites:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set Django environment
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH="$(pwd)/aristay_backend"
```

**Database Setup:**
```bash
cd aristay_backend
python manage.py migrate
python manage.py collectstatic --noinput
```

### 🐛 **Debugging Failed Tests**

**Get Full Error Traces:**
```bash
cd aristay_backend  
python -m pytest ../tests/integration/ -v --tb=long
```

**Run with Python Debugger:**
```bash
python -m pytest ../tests/integration/ --pdb
```

**Capture Print Statements:**
```bash
python -m pytest ../tests/integration/ -v -s
```

**Stop on First Failure:**
```bash
python -m pytest ../tests/integration/ -x
```

## CI/CD Integration

### 🤖 **GitHub Actions**
The project includes automated testing via GitHub Actions:

**Workflow:** `.github/workflows/backend-ci.yml`

**Triggers:**
- Push to `main` branch
- Pull requests to `main`  
- Changes to `aristay_backend/**` or `tests/**`

**Manual Trigger:**
```bash
# Push to trigger CI
git push origin mvp1_development

# Or create PR to main branch
```

### 📊 **CI Test Execution**
```yaml
# Tests run automatically with:
- Python 3.11
- SQLite database
- Proper environment variables
- Dependency caching
```

## Performance Monitoring

### ⏱️ **Test Timing**
```bash
# Time individual test categories
time python tests/production/test_production_hardening.py

# Pytest timing
cd aristay_backend
python -m pytest ../tests/integration/ --durations=10
```

### 📈 **Coverage Analysis**
```bash
cd aristay_backend
python -m pytest ../tests/ --cov=api --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Troubleshooting

### ❌ **Common Issues**

**1. Django Not Configured:**
```bash
# Solution: Set environment variables
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH="$(pwd)/aristay_backend"
```

**2. Database Errors:**
```bash
# Solution: Ensure migrations are current
cd aristay_backend
python manage.py migrate
```

**3. Import Errors:**
```bash
# Solution: Check Python path and virtual environment
which python
pip list | grep Django
```

**4. Permission Errors:**
```bash
# Solution: Check file permissions
chmod +x tests/production/test_production_hardening.py
```

### 🔍 **Validation Commands**

**Check Test Discovery:**
```bash
cd aristay_backend
python -m pytest ../tests/ --collect-only
```

**Verify Environment:**
```bash
python -c "import django; print(f'Django: {django.VERSION}')"
python -c "from api.models import Task; print('✅ Models imported successfully')"
```

**Test Database Connection:**
```bash
cd aristay_backend
python manage.py check
python manage.py showmigrations
```

## Test Development Guidelines

### ✍️ **Writing New Tests**

**Production Tests:**
- Must be hermetic (self-contained)
- Should clean up after themselves  
- Use clear, descriptive output messages

**Integration Tests:**
- Test realistic workflows
- Use proper Django test framework
- Mock external dependencies when needed

**Unit Tests:**
- Focus on single components
- Fast execution (< 1 second each)
- High coverage of edge cases

### 📝 **Test Organization**
```python
# Good test structure
class TestBookingWorkflow(TestCase):
    def setUp(self):
        # Test data setup
        
    def test_specific_scenario(self):
        # Given, When, Then pattern
        
    def tearDown(self):
        # Cleanup if needed
```

## Quick Reference

### 🎯 **Essential Commands**
```bash
# Run everything
python tests/run_tests.py

# Production tests only
python tests/production/test_production_hardening.py

# Integration tests
cd aristay_backend && python -m pytest ../tests/integration/ -v

# Unit tests  
cd aristay_backend && python -m pytest ../tests/unit/ -v

# CI-style run (from project root)
cd aristay_backend && python -m pytest ../tests/ -v --tb=short
```

### 📋 **Test Status Checklist**
- [ ] All production hardening tests passing
- [ ] Integration test suite complete
- [ ] Unit tests covering core functionality  
- [ ] CI/CD pipeline working
- [ ] No import or dependency errors

---

## 🎉 Success Indicators

**Green Test Run:**
```
🚀 ALL PRODUCTION HARDENING TESTS PASSED!
✅ Idempotent task creation working
✅ DB constraints preventing duplicates  
✅ Status mapping unified and consistent

======================== 3 passed, 0 warnings ========================
```

**Ready for Production:** All test categories passing consistently across local and CI environments.

---

*For additional support, check the `tests/README.md` file or review individual test files for specific implementation details.*
