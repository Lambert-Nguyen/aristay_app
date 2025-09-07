#!/usr/bin/env python
"""Test Cloudinary configuration switching"""

import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Test local storage (default)
os.environ.pop('USE_CLOUDINARY', None)  # Remove if exists
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
django.setup()

from django.conf import settings
print("=== LOCAL STORAGE TEST ===")
print(f"USE_CLOUDINARY: {settings.USE_CLOUDINARY}")  
print(f"Storage backend: {settings.STORAGES['default']['BACKEND']}")

# Clear Django's settings cache
from django.conf import settings as django_settings
if django_settings.configured:
    django_settings._wrapped = None

# Test Cloudinary storage
os.environ['USE_CLOUDINARY'] = 'true'
# Need to reimport settings module to pick up env changes
import importlib
if 'backend.settings' in sys.modules:
    importlib.reload(sys.modules['backend.settings'])

django.setup()

print("\n=== CLOUDINARY STORAGE TEST ===") 
print(f"USE_CLOUDINARY: {settings.USE_CLOUDINARY}")
print(f"Storage backend: {settings.STORAGES['default']['BACKEND']}")
