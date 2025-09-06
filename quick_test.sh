#!/bin/bash
# Quick Test Runner - Comprehensive system validation
# Usage: ./quick_test.sh [category]

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 ARISTAY QUICK TEST RUNNER"
echo "============================================================"

# Function to run production tests
run_production_tests() {
    echo "📋 1. PRODUCTION HARDENING TESTS"
    echo "----------------------------"
    python tests/production/test_production_hardening.py
    echo
}

# Function to run integration tests  
run_integration_tests() {
    echo "📋 2. INTEGRATION SYSTEM TESTS"
    echo "----------------------------"
    cd aristay_backend
    python -m pytest ../tests/integration/ -v --tb=short
    cd ..
    echo
}

# Function to run unit tests
run_unit_tests() {
    echo "📋 3. UNIT COMPONENT TESTS" 
    echo "----------------------------"
    cd aristay_backend
    python -m pytest ../tests/unit/ -v --tb=short
    cd ..
    echo
}

# Function to validate environment
validate_environment() {
    echo "🔍 ENVIRONMENT VALIDATION"
    echo "----------------------------"
    
    # Check virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        echo "⚠️  Warning: Virtual environment not detected"
        echo "   Run: source .venv/bin/activate"
    else
        echo "✅ Virtual environment: $VIRTUAL_ENV"
    fi
    
    # Check Python and Django
    python -c "import django; print(f'✅ Django {django.VERSION[0]}.{django.VERSION[1]}')" 2>/dev/null || echo "❌ Django not available"
    
    # Check database
    cd aristay_backend
    python manage.py check --database default 2>/dev/null && echo "✅ Database connection" || echo "❌ Database issues"
    cd ..
    
    echo
}

# Function to run CI-style tests
run_ci_tests() {
    echo "🤖 CI-STYLE VALIDATION"
    echo "----------------------------"
    export DJANGO_SETTINGS_MODULE=backend.settings
    export PYTHONPATH="$PROJECT_ROOT/aristay_backend"
    export DEBUG=0
    
    cd aristay_backend
    python -m pytest ../tests/ -v --tb=short
    cd ..
    echo
}

# Main execution logic
case "${1:-all}" in
    "production"|"prod"|"p")
        validate_environment
        run_production_tests
        echo "✅ Production tests complete"
        ;;
    "integration"|"int"|"i")
        validate_environment
        run_integration_tests  
        echo "✅ Integration tests complete"
        ;;
    "unit"|"u")
        validate_environment
        run_unit_tests
        echo "✅ Unit tests complete"
        ;;
    "ci")
        validate_environment
        run_ci_tests
        echo "✅ CI-style tests complete"
        ;;
    "env"|"environment")
        validate_environment
        ;;
    "all"|"")
        validate_environment
        run_production_tests
        run_integration_tests
        run_unit_tests
        
        echo "🎉 ALL TESTS COMPLETE"
        echo "============================================================"
        echo "✅ Production hardening validated"
        echo "✅ Integration workflows verified"  
        echo "✅ Unit components tested"
        echo "🚀 System ready for deployment"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [category]"
        echo
        echo "Categories:"
        echo "  all          Run all test categories (default)"
        echo "  production   Run production hardening tests only"  
        echo "  integration  Run integration system tests only"
        echo "  unit         Run unit component tests only"
        echo "  ci           Run CI-style validation"
        echo "  env          Validate environment only"
        echo "  help         Show this help message"
        echo
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 production         # Production tests only"
        echo "  $0 env               # Check environment"
        ;;
    *)
        echo "❌ Unknown category: $1"
        echo "Use '$0 help' for available options"
        exit 1
        ;;
esac
