# Aristay Property Management - AI Coding Instructions

## 🏗️ Architecture Overview

**Aristay** is a comprehensive property management system with Django REST API backend and Flutter mobile frontend, focusing on automated task management, secure JWT authentication, role-based access control, and intelligent booking import with conflict resolution.

### Core Components
- **Django Backend** (`aristay_backend/`): REST API with JWT auth, task automation, booking management, Excel import
- **Flutter Frontend** (`aristay_flutter_frontend/`): Mobile app for property managers and staff  
- **JWT Security System**: Custom rate-limited auth with token ownership verification
- **Task Automation**: Template-driven task creation from booking imports
- **Role-Based Access**: Dynamic permissions with custom decorators and viewsets
- **Booking Import System**: Excel/CSV import with intelligent conflict detection and resolution

### 📁 File Placement Guardrails

**Backend Service Logic**: `aristay_backend/api/services/<feature>_service.py`
**Backend Endpoints**: `aristay_backend/api/<feature>_views.py` (+ urls.py registration)
**Admin/HTML Templates**: `aristay_backend/api/templates/<area>/...`
**Security & JWT**: `aristay_backend/api/auth_views.py`, throttling in `api/throttles.py`
**Documentation**: `docs/<area>/...` exactly as specified in PROJECT_STRUCTURE.md
**Tests**:
- Unit: `tests/unit/test_<thing>.py`
- Integration: `tests/integration/test_<flow>.py`
- Security: `tests/security/test_<topic>.py`
- Booking: `tests/booking/test_<capability>.py`

**Flutter**:
- Screens: `lib/screens/<feature>_screen.dart`
- Widgets: `lib/widgets/<component>.dart`
- Services: `lib/services/<service>.dart`
- Models: `lib/models/<entity>.dart`

## 🔐 Authentication Patterns

**JWT Implementation**: Uses `djangorestframework-simplejwt` with custom security enhancements:

```python
# Custom JWT views with rate limiting and ownership verification
from api.throttles import RefreshTokenJtiRateThrottle
from api.jwt_auth_views import SecureTokenObtainPairView  # or api.auth_views.CustomTokenObtainPairView depending on project layout

# Rate limiting by JWT ID (jti), not IP - prevents token abuse
class RefreshTokenJtiRateThrottle(SimpleRateThrottle):
    scope = 'token_refresh'  # 2/minute limit
```

**Critical Security Pattern**: Always verify token ownership before revocation in `api/jwt_auth_views.py:revoke_token()`. Tokens can only be revoked by their owners.

**Authentication Flow**:
1. `POST /api/token/` → Get access/refresh tokens
2. Use `Authorization: Bearer <access_token>` 
3. `POST /api/token/refresh/` → Refresh when expired (JTI-based rate limiting)
4. `POST /api/token/revoke/` → Blacklist specific token

## 🤖 Task Automation System

**Core Pattern**: Template-driven task creation using `AutoTaskTemplate` model in `api/models.py:1782`:

```python
# Task templates with conditional logic and timing
class AutoTaskTemplate(models.Model):
    timing_type = models.CharField(choices=[
        ('before_checkin', 'Days Before Check-in'),
        ('after_checkout', 'Days After Check-out'),
    ])
    # Template rendering with booking context
    def create_task_for_booking(self, booking):
        context = {
            'property': booking.property.name,
            'guest_name': booking.guest_name,
            'check_in_date': booking.check_in_date.strftime('%Y-%m-%d'),
        }
        title = self.title_template.format(**context)
```

**Idempotent Task Creation**: Always use `get_or_create()` with `created_by_template` field to prevent duplicates.

## 🔑 Permission System Architecture

**Dynamic Permissions**: Custom permission classes in `api/permissions.py` that integrate with Django's system:

```python
# Pattern: Dynamic permissions based on user profile and context
class DynamicTaskPermissions(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check user profile permissions + object-specific rules
        return can_edit_task(request.user, obj)
```

**Authorization Helper**: Use `api/authz.py:AuthzHelper` for centralized permission checking:
- `can_edit_task(user, task)` - Checks ownership, assignment, or role permissions
- `@staff_or_perm('permission_name')` decorator for views
- Profile-based permissions via `user.profile.has_permission()`

## 📱 Flutter Frontend Architecture

**Service Layer Pattern**: Central API communication through singleton services in `aristay_flutter_frontend/lib/services/`:

```dart
// API service with token management and error handling
class ApiService {
  static const String baseUrl = 'http://192.168.1.40:8000/api';
  
  Future<List<Task>> fetchTasks({Map<String, String>? filters}) async {
    // JWT token from SharedPreferences with null safety
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token');
    if (token == null) throw AuthException('Not authenticated');
    // Centralized error handling with ValidationException
  }
}
```

**Mobile Environment Configuration**: Use Flutter build flavors with `--dart-define`:
```bash
# Development
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api

# Staging  
flutter run --dart-define=API_BASE_URL=https://staging.aristay.com/api

# Production
flutter run --dart-define=API_BASE_URL=https://api.aristay.com/api
```

**Screen-Widget Architecture**: Organized by feature with reusable components:
- `lib/screens/` - Full-screen views (HomeScreen, TaskDetailScreen, LoginScreen)
- `lib/widgets/` - Reusable components (StatusPill, UnreadBadge, TaskFilterBar)
- `lib/models/` - Data models with JSON serialization (Task, User, Property)
- `lib/services/` - Business logic (ApiService, NotificationService, NavigationService)

**State Management Pattern**: StatefulWidget with RouteAware for lifecycle management:
```dart
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with RouteAware {
  // Service injection pattern
  final _api = ApiService();
  
  // Loading/error state pattern
  bool _loading = true;
  String? _error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (route != null) routeObserver.subscribe(this, route);
  }

  @override
  void dispose() {
    routeObserver.unsubscribe(this);
    super.dispose();
  }
  
  // Data refresh on route awareness
  @override
  void didPopNext() => _refresh();
}

// In MaterialApp registration:
MaterialApp(
  navigatorObservers: [routeObserver],
  // ...
);
```

**Remember**: Keep `routeObserver` as a single shared instance and include it in `MaterialApp.navigatorObservers`.

**Widget Design System**: Consistent styling with theme-aware components:
```dart
// StatusPill widget with dynamic theming
class StatusPill extends StatelessWidget {
  static const _bases = {
    'pending': Color(0xFFFFC107),     // amber
    'in-progress': Color(0xFF64B5F6), // blue 300
    'completed': Color(0xFF81C784),   // green 300
  };
  
  // Theme-aware color calculation for dark/light mode
  final bg = isDark ? base.withValues(alpha: .18) : base.withValues(alpha: .20);
}
```

## 📊 Booking Import & Conflict Resolution System

**Enhanced Excel Import Architecture**: Multi-stage processing with intelligent conflict detection in `api/services/enhanced_excel_import_service.py`:

### **Stage 1: Data Extraction with Smart Code Generation**
```python
class EnhancedExcelImportService(ExcelImportService):
    def _extract_booking_data_enhanced(self, row, row_number: int) -> Optional[Dict]:
        # Handle generic booking sources (not real confirmation codes)
        generic_sources = ['directly', 'direct', 'owner staying', 'owner', 'walk-in']
        if external_code.lower() in generic_sources:
            # Generate unique codes for direct bookings using secure randomness
            external_code = _generate_direct_booking_code()  # uses secrets
```

### **Stage 2: Conflict Detection with Confidence Scoring**
```python
class BookingConflict:
    def _calculate_confidence(self) -> float:
        """Calculate confidence that these are the same booking (0.0 - 1.0)"""
        score = 0.0
        # External code match (highest weight) - 0.4
        # Guest name match - 0.3  
        # Property match - 0.2
        # Date overlap - 0.1
        return score
```

**Conflict Types and Auto-Resolution**:
- **Platform Bookings** (Airbnb, VRBO): Status-only changes auto-update existing bookings
- **Direct Bookings**: All conflicts require manual review
- **Exact Duplicates**: Automatically skipped with logging
- **Guest Name Changes**: Always require manual review (per business requirement)

### **Stage 3: Interactive Conflict Resolution Interface**
HTML templates in `api/templates/admin/`:
- `enhanced_excel_import.html` - Upload interface with progress tracking
- `conflict_resolution.html` - Side-by-side comparison with bulk actions

**Resolution Options**:
```javascript
// Bulk resolution patterns
resolveAllConflicts('update_existing') // Update all existing bookings
resolveAllConflicts('create_new')      // Create all as new bookings  
resolveAllConflicts('skip')            // Skip all conflicts
```

### **Stage 4: Scoped External Code Uniqueness**
```python
# Prevent duplicates within (property, source, external_code) scope
def _create_booking(self, booking_data: Dict, property_obj: Property, row) -> Booking:
    original_code = booking_data.get('external_code', '')
    source = _normalize_source(booking_data.get('source', ''))
    
    # Ensure unique external_code within property + source scope
    code = original_code
    i = 1
    while Booking.objects.filter(
        property=property_obj,
        source__iexact=source,
        external_code=code
    ).exists():
        i += 1
        code = f"{original_code} #{i}"
```

**Database Constraints**: Enforce uniqueness at the database layer with conditional constraints:
```python
# In Booking model Meta class
from django.db.models import Q, UniqueConstraint

constraints = [
    models.UniqueConstraint(
        fields=['property', 'source', 'external_code'],
        name='uniq_booking_src_code_per_property',
        condition=Q(is_deleted=False),
    ),
]
```

**Secure Code Generation**: Use cryptographically strong random generation:
```python
import secrets
from django.db import transaction, IntegrityError

def _generate_direct_booking_code() -> str:
    return f"DIR{secrets.randbelow(10**6):06d}"

@transaction.atomic
def create_booking_with_unique_code(booking_data: Dict) -> Booking:
    """Create booking with scoped uniqueness and bounded retry"""
    original_code = booking_data.get('external_code') or _generate_direct_booking_code()
    
    for attempt in range(1, 6):  # Max 5 attempts
        try:
            code = original_code if attempt == 1 else f"{original_code} #{attempt}"
            booking_data['external_code'] = code
            return Booking.objects.create(**booking_data)
        except IntegrityError:
            continue
    raise Exception("Failed to create booking with unique code after 5 attempts")
```

**Import Session Management**: Each import gets unique session ID with complete audit trail in `AuditEvent` model.

## 📊 Data Flow Patterns

**Soft Delete**: All models inherit from `SoftDeleteMixin` with `is_deleted` field. Use `objects` manager (excludes deleted) vs `all_objects` (includes deleted).

**Audit Trail**: History tracking in JSON fields with automatic change logging:
```python
# Pattern used in Property.save()
changes.append(f"{timezone.now().isoformat()}: {user_name} changed...")
hist = json.loads(old.history or "[]")
self.history = json.dumps(hist + changes)
```

**Signal-Based Automation**: Task creation triggered by booking imports via Django signals in `api/models.py` bottom section.

## 🧪 Development Workflows

**Testing Structure**: Organized by scope in `tests/` directory:
- `tests/security/` - JWT auth, permissions, throttling  
- `tests/integration/` - End-to-end workflows
- `tests/production/` - Production readiness, constraints
- `tests/api/` - API endpoint testing with authentication

**Test Commands**:
```bash
# Central test runner with categories
python tests/run_tests.py --security
python tests/run_tests.py --production

# Quick comprehensive validation  
./scripts/testing/quick_test.sh

# JWT system verification
chmod +x scripts/testing/jwt_smoke_test_improved.sh
./scripts/testing/jwt_smoke_test_improved.sh
```

**Environment Setup**:
```bash
# Project follows specific virtual env pattern
source .venv/bin/activate
cd aristay_backend && python manage.py runserver

# Or use Makefile shortcuts
make setup && make run
```

**Environment Variables**: Key configurations in `.env`:
```bash
# Caching / throttling
REDIS_URL=redis://127.0.0.1:6379/1

# JWT / security
JWT_SIGNING_KEY=change_me
SENTRY_DSN=
DJANGO_ENVIRONMENT=development
```

## 📁 Proper File Placement Guidelines

### **Documentation Structure** (per `PROJECT_STRUCTURE.md`):
```
docs/
├── security/           # Security implementations, JWT docs, permission guides
├── reports/           # Status reports, completion summaries, validation evidence  
├── implementation/    # Feature implementations, integration guides
├── features/         # Feature-specific documentation
├── testing/          # Testing guides, manual procedures
├── backend/          # Backend architecture, API documentation
└── requirements/     # Requirements specifications, PRDs
```

### **Scripts Organization**:
```
scripts/
├── testing/          # Test automation, validation scripts
├── admin/           # Database management, user administration
└── deployment/      # Production deployment, environment setup
```

### **Backend Structure**:
```
aristay_backend/
├── api/
│   ├── models.py           # Core models with SoftDeleteMixin, AutoTaskTemplate
│   ├── jwt_auth_views.py   # Secure JWT implementation with rate limiting
│   ├── permissions.py      # Dynamic permission classes
│   ├── throttles.py        # JTI-based rate limiting
│   ├── staff_views.py      # Staff dashboard with task management
│   ├── services/          # Business logic services
│   │   ├── enhanced_excel_import_service.py  # Conflict resolution system
│   │   └── excel_import_service_backup.py    # Legacy backup
│   └── templates/admin/   # HTML templates for import interfaces
├── tests/            # Organized by test category
│   ├── security/    # JWT, permissions, throttling tests
│   ├── api/         # API endpoint tests
│   └── production/  # Production hardening tests
└── backend/         # Django project settings
```

### **Frontend Structure**:
```
aristay_flutter_frontend/
├── lib/
│   ├── main.dart           # App entry point with Firebase integration
│   ├── screens/           # Full-screen views by feature
│   │   ├── home_screen.dart
│   │   ├── task_detail_screen.dart
│   │   └── login_screen.dart
│   ├── widgets/           # Reusable UI components
│   │   ├── status_pill.dart
│   │   ├── unread_badge.dart
│   │   └── task_filter_bar.dart
│   ├── services/          # Business logic and API communication
│   │   ├── api_service.dart
│   │   ├── notification_service.dart
│   │   └── navigation_service.dart
│   ├── models/           # Data models with JSON serialization
│   │   ├── task.dart
│   │   ├── user.dart
│   │   └── property.dart
│   └── utils/           # Utility classes and helpers
│       ├── api_error.dart
│       └── theme.dart
└── assets/             # Images, fonts, static resources
```

**File Naming Conventions**:
- **Tests**: `test_<functionality>.py` in appropriate category directory
- **Documentation**: `<FEATURE>_<TYPE>.md` with descriptive names
- **Scripts**: `<action>_<target>.sh` with executable permissions
- **Flutter**: `snake_case.dart` for all Dart files

## 🔧 Critical Integration Points

**Rate Limiting**: Uses Redis-backed throttling with custom scopes:
- Login: 5/minute per IP  
- Token refresh: 2/minute per JWT ID (not IP!)
- API calls: 1000/hour per user

**Cache Backend**: Development uses LocMem cache (resets on restart), production uses Redis via `REDIS_URL` (persistent across deployments).

**Cache Backend**: Development uses LocMem cache (resets on restart), production uses Redis via `REDIS_URL` (persistent across deployments).

**Database Constraints**: Production-hardened with PostgreSQL exclusion constraints and idempotency checks. Always test with `tests/production/test_production_hardening.py`.

**File Upload Security**: Images validated through `api/models.py:validate_task_image()` with 5MB limit and type checking.

## 🚨 Common Pitfalls to Avoid

1. **Don't rate limit by IP for JWT refresh** - Use JTI-based throttling to prevent token rotation attacks
2. **Always verify token ownership** before revocation - Never allow cross-user token manipulation  
3. **Use soft delete consistently** - Check `is_deleted=False` in all queries
4. **Template context safety** - Sanitize all user inputs in task template rendering
5. **Idempotent operations** - Use `get_or_create()` for automated task creation
6. **Proper file placement** - Follow `PROJECT_STRUCTURE.md` organization guidelines
7. **Flutter state management** - Always use RouteAware for proper lifecycle handling
8. **Booking conflict resolution** - Guest name changes always require manual review

## 📁 Key Files for Context

- `api/models.py` - Core models with soft delete, audit trails, task templates
- `api/jwt_auth_views.py` - Secure JWT implementation with rate limiting
- `api/permissions.py` - Dynamic permission classes  
- `api/throttles.py` - Custom JTI-based rate limiting
- `api/staff_views.py` - Staff dashboard with task management
- `api/services/enhanced_excel_import_service.py` - Booking conflict resolution system
- `PROJECT_STRUCTURE.md` - Official project organization
- `tests/run_tests.py` - Central test orchestration
- `aristay_flutter_frontend/lib/main.dart` - Flutter app entry point
- `aristay_flutter_frontend/lib/services/api_service.dart` - Mobile API layer

## 💡 Development Philosophy

Focus on **security-first design** with comprehensive rate limiting, **idempotent operations** for reliability, **template-driven automation** for flexibility, **organized file structure** following PROJECT_STRUCTURE.md, and **conflict-aware booking management** with intelligent resolution. All changes should include tests and maintain backward compatibility with existing JWT tokens.
