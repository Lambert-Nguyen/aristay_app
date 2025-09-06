"""
Global pytest configuration for Django integration.
Ensures Django is properly setup before test collection begins.
"""

import os
import sys
from pathlib import Path

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / 'aristay_backend'

# Add the backend directory to Python path for imports
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Set DJANGO_SETTINGS_MODULE if not already set
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'

# Import and setup Django before any tests run
import django
from django.conf import settings

def setup_django():
    """Ensure Django is properly configured and ready for testing."""
    if not settings.configured:
        django.setup()
    else:
        # Django is already configured, just ensure apps are loaded
        django.setup()

# Setup Django immediately when conftest.py is loaded
setup_django()
