#!/bin/bash

# Setup Local Development Environment (Heroku-compatible)
# This script sets up a local development environment that mirrors Heroku production
# 
# Usage: ./scripts/development/setup_local_dev.sh
# 
# What it does:
# 1. Installs PostgreSQL if not present
# 2. Creates local database (aristay_local)
# 3. Runs Django migrations
# 4. Sets up local development configuration

echo "🚀 Setting up local development environment..."

# 1. Install PostgreSQL if not already installed
if ! command -v psql &> /dev/null; then
    echo "📦 Installing PostgreSQL..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install postgresql
        brew services start postgresql
    else
        # Linux
        sudo apt-get update
        sudo apt-get install postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    fi
else
    echo "✅ PostgreSQL already installed"
fi

# 2. Create local database
echo "🗄️ Creating local database..."
createdb aristay_local 2>/dev/null || echo "Database aristay_local already exists"

# 3. Set up environment variables for local development
echo "⚙️ Setting up environment variables..."

# 4. Activate virtual environment and run migrations
echo "🔄 Activating virtual environment and running migrations..."
source .venv/bin/activate
cd aristay_backend

# Set environment variables and run migrations
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

echo "Using DATABASE_URL: $DATABASE_URL"
python manage.py migrate --settings=backend.settings_local

# 5. Create superuser (optional)
echo "👤 Creating superuser (optional)..."
echo "You can create a superuser by running: python manage.py createsuperuser --settings=backend.settings_local"

# 6. Load test data (optional)
echo "📊 Loading test data (optional)..."
echo "You can load test data by running: python manage.py seed_test_data --settings=backend.settings_local"

echo "✅ Local development environment setup complete!"
echo ""
echo "To start development:"
echo "1. ./scripts/development/dev_local.sh"
echo ""
echo "Your app will be available at: http://127.0.0.1:8000"