#!/usr/bin/env bash
set -euo pipefail

# Navigate to repo root
cd "$(dirname "$0")"

# Create venv if it doesn't exist
if [[ ! -f ".venv/bin/activate" ]]; then 
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r aristay_backend/requirements.txt

# Set Django settings
export DJANGO_SETTINGS_MODULE=backend.settings

# Navigate to backend and run server
cd aristay_backend
python manage.py runserver 0.0.0.0:8000
