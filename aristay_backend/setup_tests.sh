#!/bin/bash

# AriStay Backend Test Setup Script
# This script sets up everything needed to run tests locally

set -e  # Exit on any error

echo "🚀 Setting up AriStay Backend Test Environment"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the aristay_backend directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Python version: $python_version"

if [ "$(printf '%s\n' "3.9" "$python_version" | sort -V | head -n1)" != "3.9" ]; then
    echo "⚠️  Warning: Python 3.9+ recommended, you have $python_version"
fi

# Install/upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install testing dependencies
echo "🧪 Installing testing dependencies..."
pip install coverage pytest-django pytest-cov flake8 black isort safety bandit

# Set up environment variables
echo "🔧 Setting up environment variables..."
export DJANGO_SETTINGS_MODULE=backend.test_settings
export SECRET_KEY=test-secret-key-for-local-testing
export DEBUG=True

echo "DJANGO_SETTINGS_MODULE=backend.test_settings" > .env.test
echo "SECRET_KEY=test-secret-key-for-local-testing" >> .env.test
echo "DEBUG=True" >> .env.test

# Create test database and run migrations
echo "🗄️  Setting up test database..."
python manage.py migrate --settings=backend.test_settings

# Run Django system check
echo "🔍 Running Django system check..."
python manage.py check --settings=backend.test_settings

# Make test runner executable
echo "⚙️  Making test runner executable..."
chmod +x run_tests.py

# Run a quick test to verify setup
echo "🧪 Running a quick test to verify setup..."
python manage.py test tests.test_models.PropertyModelTest.test_property_creation --settings=backend.test_settings --verbosity=0

echo ""
echo "✅ Setup complete! Here's how to run tests:"
echo ""
echo "🚀 Run all tests:"
echo "   ./run_tests.py"
echo ""
echo "🎯 Run specific test suites:"
echo "   python manage.py test tests.test_models --settings=backend.test_settings"
echo "   python manage.py test tests.test_api_views --settings=backend.test_settings"
echo "   python manage.py test tests.test_permissions --settings=backend.test_settings"
echo "   python manage.py test tests.test_services --settings=backend.test_settings"
echo "   python manage.py test tests.test_integration --settings=backend.test_settings"
echo ""
echo "📊 Run tests with coverage:"
echo "   coverage run --source='.' manage.py test tests/ --settings=backend.test_settings"
echo "   coverage report"
echo "   coverage html  # Creates HTML report in htmlcov/"
echo ""
echo "🔍 Run code quality checks:"
echo "   flake8 ."
echo "   black --check ."
echo "   isort --check-only ."
echo ""
echo "🔒 Run security checks:"
echo "   safety check"
echo "   bandit -r ."
echo ""
echo "📋 For more details, see TESTING.md"
echo ""
echo "Happy testing! 🎉"
