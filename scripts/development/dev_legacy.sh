#!/bin/bash

# Start Local Development Server (Heroku-compatible)
echo "🚀 Starting local development server..."

# Set environment variables for local development
export DATABASE_URL="postgres://postgres:postgres@127.0.0.1:5432/aristay_local"
export DEBUG=true
export DJANGO_ENVIRONMENT=development
export SECRET_KEY="local-dev-secret-key-change-me"
export JWT_SIGNING_KEY="local-jwt-key-change-me"
export ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0"
export CORS_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
export CSRF_TRUSTED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
export EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
export LOAD_DOTENV=true

# Activate virtual environment and start server
source .venv/bin/activate
cd aristay_backend
python manage.py runserver 0.0.0.0:8000
