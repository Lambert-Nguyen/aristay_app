#!/bin/bash

# Start Local Development Server (Heroku-compatible with PostgreSQL)
# This script starts the Django development server with PostgreSQL database
# 
# Usage: ./scripts/development/dev_local.sh
# 
# What it does:
# 1. Activates virtual environment
# 2. Uses local PostgreSQL (no custom settings module needed)
# 3. Starts Django development server
# 4. Enables debug mode

echo "🚀 Starting local development server with PostgreSQL..."

# Activate virtual environment
source .venv/bin/activate

# Ensure PostgreSQL env vars (override with your own if desired)
export POSTGRES_DB=${POSTGRES_DB:-aristay_local}
export POSTGRES_USER=${POSTGRES_USER:-postgres}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
export POSTGRES_HOST=${POSTGRES_HOST:-127.0.0.1}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Change to backend directory and start server with default settings
cd aristay_backend

# Apply migrations before running
python manage.py migrate --noinput

# Start server
python manage.py runserver 0.0.0.0:8000