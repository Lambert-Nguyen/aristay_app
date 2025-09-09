#!/bin/bash

# Start Local Development Server (Heroku-compatible with PostgreSQL)
# This script starts the Django development server with PostgreSQL database
# 
# Usage: ./scripts/development/dev_local.sh
# 
# What it does:
# 1. Activates virtual environment
# 2. Uses local PostgreSQL settings
# 3. Starts Django development server
# 4. Enables debug mode

echo "🚀 Starting local development server with PostgreSQL..."

# Activate virtual environment
source .venv/bin/activate

# Change to backend directory and start server with local settings
cd aristay_backend
python manage.py runserver 0.0.0.0:8000 --settings=backend.settings_local