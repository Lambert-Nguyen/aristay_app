#!/usr/bin/env python3
"""
Robust production readiness verification (imports instead of hardcoded paths).
"""

import os, sys
from pathlib import Path
from uuid import uuid4

# Project root: .../aristay_app
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "aristay_backend"
sys.path.insert(0, str(BACKEND))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
from api.models import Task, Property, TaskImage
from api.staff_views import cleaning_dashboard
from api.views import TaskImageDetailView


def main():
    print("🚀 Production Readiness Verification")
    print("==================================================")
    passed = 0
    total = 6
    
    # Create unique identifiers for this test run
    unique = uuid4().hex[:8]
    user = None  # Declare at function scope

    # 1) Timedelta import fix (call the view; no AttributeError on timedelta)
    try:
        rf = RequestFactory()
        user = User.objects.create_user(username=f"verify_user_{unique}", password="x")
        req = rf.get("/staff/cleaning/")
        req.user = user
        cleaning_dashboard(req)
        print("\n1. 🕐 Checking timedelta import fix...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n1. 🕐 Checking timedelta import fix...\n   ❌ {e}")

    # 2) TaskImage queryset constraint (scoped by task_pk)
    try:
        if not user:  # Create user if first test failed
            user = User.objects.create_user(username=f"verify_user_backup_{unique}", password="x")
        prop = Property.objects.create(name=f"Verify Prop {unique}", address="x")
        task1 = Task.objects.create(title=f"t1_{unique}", property=prop, assigned_to=user, status="pending")
        task2 = Task.objects.create(title=f"t2_{unique}", property=prop, assigned_to=user, status="pending")
        img1 = TaskImage.objects.create(task=task1, image="a.jpg", uploaded_by=user)
        img2 = TaskImage.objects.create(task=task2, image="b.jpg", uploaded_by=user)

        view = TaskImageDetailView()
        view.kwargs = {"task_pk": task1.pk}
        qs = view.get_queryset()
        assert img1 in qs and img2 not in qs

        print("\n2. 🔒 Checking TaskImage queryset constraint...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n2. 🔒 Checking TaskImage queryset constraint...\n   ❌ {e}")

    # 3) Production settings presence
    try:
        assert getattr(settings, "SECRET_KEY", None)
        assert hasattr(settings, "DEBUG")
        print("\n3. ⚙️  Checking production settings...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n3. ⚙️  Checking production settings...\n   ❌ {e}")

    # 4) CORS middleware configuration
    try:
        assert "corsheaders.middleware.CorsMiddleware" in settings.MIDDLEWARE
        cors_index = settings.MIDDLEWARE.index("corsheaders.middleware.CorsMiddleware")
        assert cors_index < 3
        assert hasattr(settings, "CORS_ALLOW_ALL_ORIGINS") or hasattr(settings, "CORS_ALLOWED_ORIGINS")
        print("\n4. 🌐 Checking CORS middleware configuration...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n4. 🌐 Checking CORS middleware configuration...\n   ❌ {e}")

    # 5) Critical imports check (AST-based) - Focus on most critical duplicates
    try:
        import inspect, ast, importlib
        mod = importlib.import_module("api.views")
        tree = ast.parse(inspect.getsource(mod))
        seen, critical_dups, all_dups = set(), set(), set()
        
        # Only flag critical duplicates that could cause real issues
        critical_modules = [
            'datetime', 'django.contrib.auth.models', 'django.core.exceptions'
        ]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.names:
                    key = (node.module, tuple(sorted(a.name for a in node.names if a.name)))
                    if key in seen:
                        all_dups.add(key)
                        if node.module in critical_modules:
                            critical_dups.add(key)
                    seen.add(key)
        
        if critical_dups:
            print(f"\n5. 📦 Checking for critical duplicate imports...\n   ❌ Found critical duplicates: {list(critical_dups)}")
        else:
            print("\n5. 📦 Checking for critical duplicate imports...\n   ✅ No critical duplicates detected")
            passed += 1
            
        # Show non-critical duplicates as warnings (non-blocking)
        non_critical_dups = all_dups - critical_dups
        if non_critical_dups:
            print(f"\n⚠️  Non-critical duplicate imports (info only):")
            for dup in sorted(non_critical_dups):
                print(f"   • {dup[0]} imports {', '.join(dup[1])}")
                
    except Exception as e:
        print(f"\n5. 📦 Checking for critical duplicate imports...\n   ❌ {e}")
        import traceback
        traceback.print_exc()

    # 6) Cloudinary feature flag is a boolean; if enabled, settings exist
    try:
        use_cloudinary = getattr(settings, "USE_CLOUDINARY", False)
        assert isinstance(use_cloudinary, bool)
        if use_cloudinary:
            assert hasattr(settings, "CLOUDINARY_STORAGE")
        print("\n6. ☁️  Checking Cloudinary feature flag...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n6. ☁️  Checking Cloudinary feature flag...\n   ❌ {e}")

    print("\n==================================================")
    print(f"📊 Results: {passed}/{total} checks passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
