#!/usr/bin/env python
"""
Test runner for checklist assignment system tests
"""
import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Setup Django
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def run_checklist_tests():
    """Run all checklist-related tests"""
    print("🧪 Running Checklist Assignment System Tests")
    print("=" * 50)
    
    # Test categories
    test_categories = [
        {
            'name': 'Unit Tests - Checklist Assignment',
            'pattern': 'tests/unit/test_checklist_assignment.py',
            'description': 'Core assignment logic and command functionality'
        },
        {
            'name': 'Unit Tests - Photo Upload',
            'pattern': 'tests/unit/test_checklist_photo_upload.py',
            'description': 'Photo upload and removal functionality'
        },
        {
            'name': 'Integration Tests - Workflow',
            'pattern': 'tests/integration/test_checklist_workflow.py',
            'description': 'Complete checklist workflow integration'
        },
        {
            'name': 'Integration Tests - Assignment System',
            'pattern': 'tests/integration/test_checklist_assignment_integration.py',
            'description': 'Full system integration and performance tests'
        }
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for category in test_categories:
        print(f"\n📋 {category['name']}")
        print(f"   {category['description']}")
        print("-" * 40)
        
        try:
            # Run tests for this category
            from django.test.runner import DiscoverRunner
            runner = DiscoverRunner(verbosity=2, interactive=False)
            
            # Discover and run tests
            test_suite = runner.build_suite([category['pattern']])
            result = runner.run_suite(test_suite)
            
            # Count results
            tests_run = result.testsRun
            failures = len(result.failures)
            errors = len(result.errors)
            
            total_tests += tests_run
            total_failures += failures
            total_errors += errors
            
            print(f"   ✅ Tests run: {tests_run}")
            if failures > 0:
                print(f"   ❌ Failures: {failures}")
            if errors > 0:
                print(f"   💥 Errors: {errors}")
            
            if failures == 0 and errors == 0:
                print(f"   🎉 All tests passed!")
            
        except Exception as e:
            print(f"   💥 Error running tests: {e}")
            total_errors += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests run: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("🎉 All checklist tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_checklist_tests()
    sys.exit(0 if success else 1)
