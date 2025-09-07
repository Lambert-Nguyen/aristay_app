# 🔧 Scripts Directory

This directory contains all development, testing, and administrative scripts for the Aristay project, organized by function and purpose.

## 📁 Current Script Organization

```
scripts/
├── README.md                    # This documentation
├── testing/                     # Testing and validation scripts  
│   ├── quick_test.sh           # Quick comprehensive test runner
│   ├── jwt_smoke_test.sh       # JWT authentication validation
│   └── jwt_smoke_test_improved.sh # Enhanced JWT testing
├── admin/                      # Administrative and maintenance scripts
│   ├── audit_user_access.py   # User access audit and validation
│   ├── seed_new_permissions.py # Permission system seeding
│   └── [existing admin scripts] # Legacy admin utilities
└── permissions/                # Permission management scripts
    └── [existing permission scripts] # Legacy permission tools
```
  - Permission system testing
  - API endpoint testing

## Usage

### Permission Scripts

```bash
# Grant manager portal access to a user
cd scripts/permissions
python grant_portal_access.py

# Add new permission to system
python add_manager_portal_permission.py

# Reset user password
python reset_password.py
```

### Admin Scripts

```bash
# Run cleanup tasks
cd scripts/admin
python cleanup_cron.py
```

### Demo Scripts

```bash
# Dynamic permissions demo
python conflict_demo.py

# Debug permissions
python debug_permissions.py
```

### Testing Scripts

```bash
# Test permission system
python test_permissions.py

# Test API endpoints with permissions
python test_api_permissions.py
```

## Adding New Scripts

1. Place permission-related scripts in `permissions/`
2. Place admin/maintenance scripts in `admin/`
3. Place general utilities in root `scripts/`
4. Include proper documentation and usage examples
