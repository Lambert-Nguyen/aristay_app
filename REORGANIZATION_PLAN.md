# 🏗️ PROJECT STRUCTURE REORGANIZATION PLAN

## Current Issues Identified:
1. **Test files scattered**: Root level, `tests/`, `scripts/`
2. **Documentation fragmented**: `docs/` has mixed content types
3. **Redundant files**: Multiple README files, overlapping summaries
4. **Poor categorization**: Scripts mixed with tests

## Proposed Organized Structure:

```
aristay_app/
├── README.md                              # Main project README
├── Makefile                               # Build/deployment commands
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore rules
├── .pre-commit-config.yaml               # Code quality hooks
│
├── aristay_backend/                       # Django backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── api/
│   ├── backend/
│   └── ...
│
├── aristay_flutter_frontend/              # Flutter mobile app
│   ├── pubspec.yaml
│   ├── lib/
│   └── ...
│
├── docs/                                  # 📚 All Documentation
│   ├── README.md                          # Documentation index
│   ├── setup/                             # Setup & Installation
│   │   ├── DEPLOYMENT_GUIDE.md
│   │   ├── USING_ENV_VARS.md
│   │   └── SECRET_SCANNING.md
│   ├── development/                       # Development Docs
│   │   ├── PROJECT_README.md
│   │   ├── PRODUCTION_READINESS.md
│   │   └── permission_refactoring_summary.md
│   ├── implementation/                    # Implementation Details
│   │   ├── FINAL_IMPLEMENTATION_SUMMARY.md
│   │   ├── GPT_AGENT_FIXES_COMPLETE.md
│   │   ├── AGENT_RESPONSE_IMPLEMENTATION.md
│   │   └── STATUS_UPDATE_FIX.md
│   ├── testing/                          # Testing Documentation
│   │   ├── TEST_ORGANIZATION.md
│   │   ├── END_TO_END_ACCEPTANCE_REPORT.md
│   │   └── GUEST_NAME_ANALYSIS.md
│   └── reports/                          # Final Reports
│       ├── AGENT_RECOMMENDATIONS_SUMMARY.md
│       ├── FINAL_POLISH_SUMMARY.md
│       └── PR_DIFF_SUMMARY.md
│
├── tests/                                # 🧪 All Tests
│   ├── README.md                         # Testing guide
│   ├── run_final_validation.py           # Main test runner
│   ├── production/                       # Production validation
│   │   └── test_production_hardening.py
│   ├── integration/                      # Integration tests
│   │   ├── test_final_phases.py
│   │   ├── verify_production_readiness.py
│   │   └── test_booking_conflicts.py
│   ├── unit/                            # Unit tests
│   │   ├── api/
│   │   ├── booking/
│   │   └── permissions/
│   └── tools/                           # Test utilities
│       └── test_dashboard_access.py
│
├── scripts/                             # 🔧 Utility Scripts
│   ├── README.md                        # Scripts documentation
│   ├── development/                     # Dev utilities
│   │   ├── check_auth.py
│   │   ├── debug_permissions.py
│   │   └── conflict_demo.py
│   ├── testing/                        # Test utilities
│   │   ├── test_api_permissions.py
│   │   └── test_permissions.py
│   └── admin/                          # Admin utilities
│       └── (admin scripts)
│
├── tools/                              # 🛠️ Build Tools
│   ├── dev.sh                          # Development setup
│   └── (other build tools)
│
└── assets/                             # 📁 Static Assets
    └── (images, etc.)
```

## Reorganization Steps:
1. **Clean up root level**: Move scattered files to proper locations
2. **Organize documentation**: Categorize by purpose (setup, dev, implementation, testing, reports)
3. **Consolidate tests**: All in `tests/` with clear categories
4. **Separate scripts**: Development vs testing vs admin utilities
5. **Remove duplicates**: Consolidate overlapping documentation
6. **Update references**: Fix any broken links after reorganization

## Benefits:
- ✅ Clear separation of concerns
- ✅ Easy navigation for new developers
- ✅ Logical grouping by function
- ✅ Reduced duplication
- ✅ Professional project structure
