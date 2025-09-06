# AriStay Project - Organized Structure

## 📁 Project Organization

The AriStay project has been reorganized for better maintainability and clarity.

### Root Directory Structure

```
aristay_app/
├── 📁 docs/                    # All project documentation
│   ├── features/               # Feature documentation
│   ├── fixes/                  # Bug fix documentation  
│   ├── backend/               # Backend technical docs
│   ├── requirements/          # Requirements & specs
│   └── README.md              # Documentation index
├── 📁 tests/                   # All test files
│   ├── permissions/           # Permission system tests
│   ├── api/                   # API endpoint tests
│   ├── booking/              # Booking system tests
│   └── README.md             # Testing guide
├── 📁 scripts/                 # Utility scripts
│   ├── permissions/          # Permission management
│   ├── admin/               # Administrative tools
│   └── README.md            # Script usage guide
├── 📁 assets/                  # Static assets & files
├── 📁 aristay_backend/         # Django backend (cleaned)
├── 📁 aristay_flutter_frontend/ # Flutter frontend
├── 📄 README.md               # Main project README
└── 📄 .gitignore             # Git ignore rules
```

### Backend Structure (Cleaned)

```
aristay_backend/
├── 📁 api/                     # Main Django app
├── 📁 backend/                 # Django settings
├── 📁 logs/                    # Application logs
├── 📁 media/                   # User uploaded files
├── 📁 static/                  # Static files
├── 📁 tests/                   # Django unit tests
├── 📁 __pycache__/            # Python cache
├── 📄 manage.py               # Django management
├── 📄 requirements.txt        # Python dependencies
├── 📄 db.sqlite3             # Database
└── 📄 firebase_credentials.json # Firebase config
```

## 🗂️ File Organization Changes

### Documentation
- ✅ **Moved**: All `.md` files to `docs/` with subcategories
- ✅ **Moved**: Requirements docs to `docs/requirements/`
- ✅ **Moved**: Backend docs to `docs/backend/`
- ✅ **Created**: Documentation index and guides

### Tests
- ✅ **Moved**: All `test_*.py` files to `tests/` directory
- ✅ **Organized**: Tests by functionality (permissions, api, booking)
- ✅ **Created**: Test running guide and structure documentation

### Scripts
- ✅ **Moved**: Utility scripts to `scripts/` directory
- ✅ **Organized**: Scripts by purpose (permissions, admin)
- ✅ **Created**: Usage documentation for all scripts

### Cleanup
- ✅ **Removed**: Empty artifact directories (`#/`, `first/`, `or/`, `substitute/`)
- ✅ **Organized**: Assets and static files
- ✅ **Cleaned**: Root directory clutter

## 🎯 Benefits of New Structure

1. **🔍 Better Discovery**: Related files are grouped together
2. **📚 Clear Documentation**: All docs in one place with categories
3. **🧪 Organized Testing**: Tests grouped by functionality
4. **🛠️ Easy Maintenance**: Scripts organized by purpose
5. **🏗️ Standard Structure**: Follows Python/Django best practices
6. **📖 Self-Documenting**: Each directory has its own README

## 🚀 Quick Start

### Running Tests
```bash
# All tests
python -m pytest tests/

# Specific category
python -m pytest tests/permissions/
```

### Using Scripts
```bash
# Permission management
cd scripts/permissions
python grant_portal_access.py

# Admin utilities  
cd scripts/admin
python cleanup_cron.py
```

### Documentation
```bash
# View documentation index
cat docs/README.md

# Feature documentation
ls docs/features/

# Backend documentation
ls docs/backend/
```

## 📋 Migration Guide

If you have scripts or processes that reference the old file locations:

### Old → New Locations

| Old Location | New Location |
|-------------|-------------|
| `*.md` | `docs/` (categorized) |
| `test_*.py` | `tests/` (categorized) |
| `*_demo.py` | `scripts/` |
| `permission_scripts.py` | `scripts/permissions/` |
| `admin_scripts.py` | `scripts/admin/` |
| Backend `*.md` | `docs/backend/` |

### Update Your Commands
```bash
# Old
python test_permissions.py
# New  
python tests/permissions/test_manager_portal.py

# Old
python grant_access.py
# New
cd scripts/permissions && python grant_portal_access.py
```

This organization makes the project more professional, maintainable, and easier to navigate! 🎉
