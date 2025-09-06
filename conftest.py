"""
Pytest configuration for Aristay project
Ensures Django is set up before test collection
"""
import os
import sys
from pathlib import Path

# Add aristay_backend to Python path
REPO_ROOT = Path(__file__).parent
BACKEND_DIR = REPO_ROOT / "aristay_backend"
sys.path.insert(0, str(BACKEND_DIR))

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Initialize Django
import django
django.setup()
