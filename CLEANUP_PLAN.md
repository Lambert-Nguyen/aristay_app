# Project Cleanup Plan

## Issues Identified

### 1. Root Directory Clutter (23 loose files)
- **12 Chat-related files** - Should be consolidated
- **Multiple completion/fix reports** - Should be in docs/reports/
- **JavaScript diagnostic file** - Should be in tools/
- **cookies.txt files** - Should be .gitignored

### 2. Documentation Sprawl
- **75 dated files** (2025-01-08, 2025-09-10, etc.)
- **Multiple "FINAL" and "COMPLETE" reports** - Redundant/outdated
- **Duplicate documentation** - Same topics covered multiple times

### 3. Test File Disorganization
- **17 legacy_validations files** - Should be archived
- **Test files in aristay_backend root** - Should be in tests/
- **Scattered test utilities** - Needs consolidation

### 4. Script Inconsistency
- Scripts scattered across root, aristay_backend/, and scripts/
- Inconsistent naming and organization

## Cleanup Actions

### Phase 1: Root Directory Cleanup
1. **Move chat documentation** → `docs/features/chat/`
2. **Move completion reports** → `docs/reports/archive/`
3. **Move diagnostic tools** → `tools/diagnostics/`
4. **Remove duplicate cookies.txt** files
5. **Keep only**: README.md, Makefile, requirements.txt, runtime.txt, .env.example

### Phase 2: Documentation Archive
1. **Create** `docs/archive/` for outdated docs
2. **Move dated files** (older than latest version)
3. **Consolidate duplicate reports**
4. **Update DOCUMENTATION_INDEX.md**

### Phase 3: Test Organization
1. **Archive** `tests/legacy_validations/` → `tests/archive/legacy/`
2. **Move aristay_backend/*.py tests** → `tests/backend/`
3. **Consolidate test utilities** → `tests/utils/`

### Phase 4: Final Cleanup
1. **Remove obsolete files**
2. **Update .gitignore**
3. **Create new project structure docs**
4. **Verify no broken imports**

## New Structure

```
aristay_app/
├── README.md                          # Main project readme
├── Makefile                           # Build automation
├── requirements.txt                   # Python dependencies
├── runtime.txt                        # Runtime version
├── .env.example                       # Environment template
├── pytest.ini                         # Test configuration
├──aristay_backend/              # Django backend
│   ├── manage.py                     # Django management
│   ├── api/                          # API application
│   ├── backend/                      # Django settings
│   └── tests/                        # Backend-specific tests
├── aristay_flutter_frontend/         # Flutter frontend
├── docs/                             # All documentation
│   ├── README.md                     # Docs index
│   ├── DOCUMENTATION_INDEX.md        # Complete index
│   ├── api/                          # API documentation
│   ├── backend/                      # Backend guides
│   ├── features/                     # Feature docs
│   │   └── chat/                     # Chat system docs
│   ├── deployment/                   # Deployment guides
│   ├── development/                  # Dev guides
│   ├── security/                     # Security docs
│   ├── testing/                      # Testing guides
│   ├── reports/                      # Reports
│   │   ├── active/                   # Current reports
│   │   └── archive/                  # Old reports
│   └── archive/                      # Historical docs
├── tests/                            # Test suite
│   ├── conftest.py                   # Pytest config
│   ├── utils/                        # Test utilities
│   ├── backend/                      # Backend tests
│   ├── api/                          # API tests
│   ├── ui/                           # UI tests
│   ├── chat/                         # Chat tests
│   └── archive/                      # Archived tests
│       └── legacy/                   # Legacy validations
├── scripts/                          # Utility scripts
│   ├── README.md                     # Script documentation
│   ├── deployment/                   # Deployment scripts
│   ├── admin/                        # Admin scripts
│   ├── testing/                      # Test scripts
│   ├── development/                  # Dev scripts
│   └── permissions/                  # Permission scripts
└── tools/                            # Development tools
    ├── secret-hygiene/               # Secret scanning
    └── diagnostics/                  # Diagnostic tools
```

## Files to Remove

### Duplicates/Obsolete
- cookies.txt (both copies)
- aristay_backend/cookies.txt
- Multiple dated versions of same docs

### Can Be Deleted (Superseded)
- Old "FINAL" reports when newer exists
- Duplicate implementation summaries
- Test validation files for completed features
