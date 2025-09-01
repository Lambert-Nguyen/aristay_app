#!/usr/bin/env python
"""
Comprehensive test runner for AriStay Backend
Runs all tests and generates detailed reports
"""

import os
import subprocess
import sys
import time

import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.test.utils import get_runner


def setup_django():
    """Setup Django environment for testing"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")

    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()

    print(f"Duration: {end_time - start_time:.2f} seconds")

    if result.returncode == 0:
        print("✅ SUCCESS")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ FAILED")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)

    return result.returncode == 0


def main():
    """Main test runner function"""
    print("🚀 Starting AriStay Backend Test Suite")
    print(f"Python version: {sys.version}")
    print(f"Django version: {django.VERSION}")

    # Setup Django
    setup_django()

    # Test results tracking
    results = {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "test_suites": {}}

    # List of test commands to run
    test_commands = [
        {"command": "python manage.py check", "description": "Django System Check", "critical": True},
        {"command": "python manage.py check --deploy", "description": "Django Deployment Check", "critical": False},
        {
            "command": "python manage.py makemigrations --check",
            "description": "Check for pending migrations",
            "critical": True,
        },
        {"command": "python manage.py test tests.test_models --verbosity=2", "description": "Model Tests", "critical": True},
        {
            "command": "python manage.py test tests.test_api_views --verbosity=2",
            "description": "API View Tests",
            "critical": True,
        },
        {
            "command": "python manage.py test tests.test_permissions --verbosity=2",
            "description": "Permission Tests",
            "critical": True,
        },
        {
            "command": "python manage.py test tests.test_services --verbosity=2",
            "description": "Service Tests",
            "critical": False,
        },
        {
            "command": "python manage.py test tests.test_integration --verbosity=2",
            "description": "Integration Tests",
            "critical": False,
        },
        {"command": "python manage.py test api.tests --verbosity=2", "description": "Legacy API Tests", "critical": False},
    ]

    # Run existing test files if they exist
    existing_tests = [
        "test_enhanced_excel_import.py",
        "test_booking_creation.py",
        "test_nights_final.py",
        "test_nights_handling.py",
        "test_sheet_name.py",
    ]

    for test_file in existing_tests:
        if os.path.exists(test_file):
            test_commands.append(
                {"command": f"python {test_file}", "description": f"Legacy Test: {test_file}", "critical": False}
            )

    # Run all test commands
    for test_config in test_commands:
        success = run_command(test_config["command"], test_config["description"])

        results["total_tests"] += 1
        if success:
            results["passed_tests"] += 1
        else:
            results["failed_tests"] += 1
            if test_config["critical"]:
                print(f"❌ CRITICAL TEST FAILED: {test_config['description']}")

        results["test_suites"][test_config["description"]] = {
            "passed": success,
            "critical": test_config.get("critical", False),
        }

    # Generate summary report
    print(f"\n{'='*80}")
    print("🏁 TEST SUMMARY REPORT")
    print(f"{'='*80}")

    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']} ✅")
    print(f"Failed: {results['failed_tests']} ❌")
    print(f"Success Rate: {(results['passed_tests']/results['total_tests']*100):.1f}%")

    print(f"\n{'Test Suite Details':-^80}")
    for suite_name, suite_result in results["test_suites"].items():
        status = "✅ PASS" if suite_result["passed"] else "❌ FAIL"
        critical = " (CRITICAL)" if suite_result["critical"] else ""
        print(f"{suite_name:<50} {status}{critical}")

    # Check for critical failures
    critical_failures = [
        name for name, result in results["test_suites"].items() if not result["passed"] and result["critical"]
    ]

    if critical_failures:
        print(f"\n⚠️  CRITICAL FAILURES DETECTED:")
        for failure in critical_failures:
            print(f"   - {failure}")
        print("\n❌ CRITICAL TESTS FAILED - BUILD SHOULD NOT PASS")
        return 1

    if results["failed_tests"] > 0:
        print(f"\n⚠️  {results['failed_tests']} non-critical test(s) failed")
        print("✅ All critical tests passed - Build can proceed")
        return 0
    else:
        print("\n🎉 ALL TESTS PASSED!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
