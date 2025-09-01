# Scripts Directory

This directory contains utility scripts and tools for the AriStay project.

## Directory Structure

- **`permissions/`** - Permission management scripts
  - Add manager portal permission
  - Grant portal access
  - Reset user passwords

- **`admin/`** - Administrative scripts
  - Cleanup cron jobs
  - Database maintenance
  - System utilities

- **Root Scripts** - General utility scripts
  - Demo scripts
  - Debug utilities
  - Authentication check scripts

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

## Adding New Scripts

1. Place permission-related scripts in `permissions/`
2. Place admin/maintenance scripts in `admin/`
3. Place general utilities in root `scripts/`
4. Include proper documentation and usage examples
