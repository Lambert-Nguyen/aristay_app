# 🏗️ Aristay Project - Official Structure

This document defines the official organization of the Aristay project, consolidating all previous reorganization plans into a single authoritative structure.

## 📋 Project Overview

**Aristay** is a comprehensive property management system consisting of:
- **Backend**: Django REST API with JWT authentication, booking management, and task automation
- **Frontend**: Flutter mobile application for property managers and staff
- **Infrastructure**: PostgreSQL database, file storage, and production deployment tools

## 📁 Official Project Structure

```
aristay_app/
├── README.md                              # Main project documentation
├── PROJECT_STRUCTURE.md                   # This document (official structure)
├── Makefile                               # Build and development commands
├── conftest.py                           # Pytest configuration (root level required)
├── pytest.ini                           # Pytest settings
├── .env.example                          # Environment variables template
├── .gitignore                            # Git ignore rules
│
├── 🏗️ aristay_backend/                    # Django backend application
│   ├── manage.py                         # Django management script
│   ├── requirements.txt                  # Python dependencies
│   ├── api/                              # Main API application
│   │   ├── models.py                     # Database models
│   │   ├── views.py                      # API endpoints
│   │   ├── auth_views.py                 # JWT authentication endpoints
│   │   ├── staff_views.py                # Staff dashboard endpoints
│   │   ├── permissions.py                # Custom permissions
│   │   ├── throttles.py                  # API throttling
│   │   ├── urls.py                       # URL routing
│   │   ├── services/                     # Business logic services
│   │   ├── migrations/                   # Database migrations
│   │   └── management/                   # Django management commands
│   ├── backend/                          # Django project settings
│   │   ├── settings.py                   # Main settings
│   │   ├── urls.py                       # Root URL configuration
│   │   └── wsgi.py                       # WSGI configuration
│   ├── static/                           # Static files
│   ├── media/                            # User-uploaded files
│   └── logs/                             # Application logs
│
├── 📱 aristay_flutter_frontend/           # Flutter mobile application
│   ├── lib/                              # Dart source code
│   ├── assets/                           # App assets (images, fonts)
│   ├── android/                          # Android-specific code
│   ├── ios/                              # iOS-specific code
│   ├── web/                              # Web deployment files
│   └── pubspec.yaml                      # Flutter dependencies
│
├── 🧪 tests/                             # Comprehensive test suite
│   ├── README.md                         # Testing documentation
│   ├── run_tests.py                      # Central test runner
│   │
│   ├── unit/                             # Unit tests (component-specific)
│   │   ├── test_models.py                # Model validation tests
│   │   ├── test_services.py              # Service layer tests
│   │   └── test_utilities.py             # Utility function tests
│   │
│   ├── integration/                      # Integration tests (multi-component)
│   │   ├── test_final_phases.py          # Phase completion validation
│   │   ├── verify_production_readiness.py # Production readiness checks
│   │   ├── test_no_duplicate_tasks.py    # Duplicate prevention tests
│   │   └── agent_final_comprehensive_test.py # AI agent validation
│   │
│   ├── production/                       # Production readiness tests
│   │   ├── test_production_hardening.py  # Idempotence & constraints
│   │   └── test_production_readiness.py  # Production deployment validation
│   │
│   ├── api/                             # API endpoint tests
│   │   ├── test_auth_endpoints.py        # Authentication API tests
│   │   ├── test_task_api.py              # Task management API tests
│   │   └── test_staff_api.py             # Staff dashboard API tests
│   │
│   ├── security/                        # Security-focused tests
│   │   ├── test_jwt_authentication.py    # JWT security validation
│   │   ├── test_permissions.py           # Permission system tests
│   │   └── test_rate_limiting.py         # Throttling and rate limiting
│   │
│   ├── booking/                         # Booking system tests
│   │   ├── test_excel_import.py          # Excel import functionality
│   │   ├── test_booking_conflicts.py     # Conflict detection
│   │   └── test_guest_management.py      # Guest name handling
│   │
│   └── performance/                     # Performance and load tests
│       ├── test_database_performance.py  # DB query optimization
│       └── test_api_performance.py       # API response time tests
│
├── 📚 docs/                              # Comprehensive documentation
│   ├── README.md                         # Documentation index
│   ├── DOCUMENTATION_INDEX.md            # Complete documentation guide
│   │
│   ├── setup/                           # Installation & Setup
│   │   ├── INSTALLATION_GUIDE.md         # Step-by-step installation
│   │   ├── DEPLOYMENT_GUIDE.md           # Production deployment
│   │   ├── ENV_VARS_GUIDE.md             # Environment configuration
│   │   └── SECRET_MANAGEMENT.md          # Security configuration
│   │
│   ├── development/                     # Development Documentation
│   │   ├── DEVELOPMENT_SETUP.md          # Development environment
│   │   ├── API_DOCUMENTATION.md          # API endpoints reference
│   │   ├── DATABASE_SCHEMA.md            # Database design
│   │   └── CODING_STANDARDS.md           # Code style guidelines
│   │
│   ├── features/                        # Feature Documentation
│   │   ├── JWT_AUTHENTICATION.md         # JWT implementation details
│   │   ├── BOOKING_SYSTEM.md             # Booking management features
│   │   ├── TASK_AUTOMATION.md            # Automated task creation
│   │   └── PERMISSION_SYSTEM.md          # Role-based access control
│   │
│   ├── testing/                         # Testing Documentation
│   │   ├── TESTING_STRATEGY.md           # Testing approach & philosophy
│   │   ├── TEST_ORGANIZATION.md          # Test suite structure
│   │   ├── TESTING_MANUAL.md             # Manual testing procedures
│   │   └── SYSTEM_TESTING_GUIDE.md       # System-level testing
│   │
│   ├── security/                        # Security Documentation
│   │   ├── SECURITY_OVERVIEW.md          # Security architecture
│   │   ├── JWT_SECURITY_GUIDE.md         # JWT security implementation
│   │   ├── API_SECURITY.md               # API security measures
│   │   └── SECURITY_CHECKLIST.md         # Security validation checklist
│   │
│   ├── implementation/                  # Implementation Records
│   │   ├── IMPLEMENTATION_HISTORY.md     # Development timeline
│   │   ├── PHASE_COMPLETIONS.md          # Phase completion records
│   │   ├── BUG_FIXES.md                  # Major bug fix documentation
│   │   └── PRODUCTION_FIXES.md           # Production issue resolutions
│   │
│   └── reports/                         # Project Reports & Summaries
│       ├── FINAL_PROJECT_STATUS.md       # Current project status
│       ├── COMPLETION_SUMMARIES.md       # Phase completion summaries
│       ├── AGENT_ANALYSIS_REPORTS.md     # AI agent analysis results
│       └── PR_DOCUMENTATION.md           # Pull request documentation
│
├── 🔧 scripts/                           # Development & Utility Scripts
│   ├── README.md                         # Scripts documentation
│   ├── testing/                          # Testing scripts
│   │   ├── quick_test.sh                 # Quick test runner
│   │   ├── jwt_smoke_test.sh             # JWT authentication testing
│   │   └── comprehensive_test.sh         # Full system testing
│   ├── admin/                           # Administrative scripts
│   │   ├── check_auth.py                 # Authentication verification
│   │   ├── debug_permissions.py          # Permission debugging
│   │   ├── audit_user_access.py          # User access auditing
│   │   └── seed_permissions.py           # Permission data seeding
│   ├── deployment/                      # Deployment scripts
│   │   ├── deploy_staging.sh             # Staging deployment
│   │   ├── deploy_production.sh          # Production deployment
│   │   └── backup_database.sh            # Database backup
│   └── development/                     # Development utilities
│       ├── dev_setup.sh                  # Development environment setup
│       ├── reset_database.sh             # Database reset for development
│       └── generate_test_data.py         # Test data generation
│
├── 🎯 tools/                            # Development Tools & Utilities
│   ├── secret-hygiene/                   # Security tools
│   │   ├── purge_secrets.sh              # Secret scanning and cleanup
│   │   └── check_env_vars.py             # Environment validation
│   ├── database/                        # Database tools
│   │   └── migration_helper.py           # Migration utilities
│   └── dev.sh                           # Main development script
│
└── 🖼️ assets/                           # Shared Project Assets
    ├── README.md                         # Asset documentation
    ├── images/                          # Project images & screenshots
    ├── diagrams/                        # Architecture diagrams
    └── templates/                       # Document templates
```

## 🎯 Key Organizational Principles

### 1. **Clear Separation of Concerns**
- **Application Code**: `aristay_backend/`, `aristay_flutter_frontend/`
- **Testing**: `tests/` (organized by test type and scope)
- **Documentation**: `docs/` (organized by audience and purpose)
- **Automation**: `scripts/` (organized by function)
- **Tools**: `tools/` (development utilities)

### 2. **Consistent Documentation Structure**
- Each major directory has a `README.md` explaining its contents
- Documentation is organized by purpose: setup, development, features, security
- All implementation details are documented in `docs/implementation/`
- Final reports and summaries are in `docs/reports/`

### 3. **Comprehensive Test Organization**
- Tests are organized by scope: unit → integration → production
- Each test category has clear responsibilities
- Central test runner (`tests/run_tests.py`) orchestrates all testing
- Security tests are isolated for focused security validation

### 4. **Script Organization by Purpose**
- Testing scripts for automated validation
- Admin scripts for system management  
- Deployment scripts for production processes
- Development scripts for local development

## 🚀 Migration Plan

This structure represents the target organization. Files will be moved from their current scattered locations to this organized structure while maintaining all functionality and updating all references.

## 📊 Success Metrics

- **Zero scattered files** at root level (except essential ones)
- **Consistent documentation** structure throughout
- **Comprehensive test organization** with clear categorization
- **Centralized script management** with proper organization
- **Clear separation** between different types of content

---

*This document serves as the single source of truth for project organization. All future development should follow this structure.*
