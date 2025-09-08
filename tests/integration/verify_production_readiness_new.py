#!/usr/bin/env python3
"""
Robust production readiness verification (imports instead of hardcoded paths).
"""

import os, sys
from pathlib import Path

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

    # 1) Timedelta import fix (call the view; no AttributeError on timedelta)
    try:
        rf = RequestFactory()
        user = User.objects.create_user(username="verify_user", password="x")
        req = rf.get("/staff/cleaning/")
        req.user = user
        cleaning_dashboard(req)
        print("\n1. 🕐 Checking timedelta import fix...\n   ✅ OK")
        passed += 1
    except Exception as e:
        print(f"\n1. 🕐 Checking timedelta import fix...\n   ❌ {e}")

    # 2) TaskImage queryset constraint (scoped by task_pk)
    try:
        prop = Property.objects.create(name="Verify Prop", address="x")
        task1 = Task.objects.create(title="t1", property_ref=prop, assigned_to=user, status="pending")
        task2 = Task.objects.create(title="t2", property_ref=prop, assigned_to=user, status="pending")
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

    # 5) Duplicate imports in api.views (AST-based, not path-based)
    try:
        import inspect, ast, importlib
        mod = importlib.import_module("api.views")
        tree = ast.parse(inspect.getsource(mod))
        seen, dups = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                key = (node.module, tuple(sorted(a.name for a in node.names)))
                (dups if key in seen else seen).add(key) if key in seen else None
                seen.add(key)
        assert not dups
        print("\n5. 📦 Checking for duplicate imports...\n   ✅ None detected")
        passed += 1
    except Exception as e:
        print(f"\n5. 📦 Checking for duplicate imports...\n   ❌ {e}")

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
