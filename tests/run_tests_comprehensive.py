#!/usr/bin/env python3
"""
Comprehensive Test Runner for Aristay Project
Runs all tests in the organized test structure according to PROJECT_STRUCTURE.md
"""
import os
import sys
import subprocess
from pathlib import Path

# Project root directory  
PROJECT_ROOT = Path(__file__).parent.parent  # Go up to /Users/.../aristay_app
BACKEND_DIR = PROJECT_ROOT / "aristay_backend"
TESTS_DIR = PROJECT_ROOT / "tests"

def run_command(cmd, cwd=None):
    """Run a shell command and return the result"""
    print(f"🏃 Running: {' '.join(cmd)}")
    if cwd:
        print(f"📍 Directory: {cwd}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        print(f"✅ Success: {' '.join(cmd)}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        # Handle exit code 5 (no tests found) as success
        if e.returncode == 5:
            print(f"⚠️  No tests found: {' '.join(cmd)}")
            return True
        print(f"❌ Failed: {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def get_python_executable():
    """Get the correct Python executable path"""
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return "python"

def run_unit_tests():
    """Run unit tests (component-specific)"""
    print("\n🧩 RUNNING UNIT TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "unit" / "test_models.py",
        TESTS_DIR / "unit" / "test_assign_task_groups_command.py",
        TESTS_DIR / "unit" / "test_task_group_functionality.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_api_tests():
    """Run API endpoint tests"""
    print("\n🌐 RUNNING API TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "api" / "test_auth_endpoints.py",
        TESTS_DIR / "api" / "test_api.py",
        TESTS_DIR / "api" / "test_audit_api.py",
        TESTS_DIR / "api" / "test_task_image_api.py",
        TESTS_DIR / "api" / "test_staff_api.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_security_tests():
    """Run security-focused tests"""
    print("\n🔒 RUNNING SECURITY TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "security" / "test_jwt_security.py",
        TESTS_DIR / "security" / "test_jwt_clean.py",
        TESTS_DIR / "security" / "test_jwt_system.py",
        TESTS_DIR / "security" / "test_permissions.py",
        TESTS_DIR / "security" / "test_manager_permissions.py",
        TESTS_DIR / "security" / "test_dynamic_permissions.py",
        TESTS_DIR / "security" / "test_safety_checks.py",
        TESTS_DIR / "security" / "test_security_fixes.py",
        TESTS_DIR / "security" / "test_audit_events.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_booking_tests():
    """Run booking system tests"""
    print("\n📅 RUNNING BOOKING TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "booking" / "test_excel_import.py",
        TESTS_DIR / "booking" / "test_booking_conflicts.py",
        TESTS_DIR / "booking" / "test_booking_creation.py",
        TESTS_DIR / "booking" / "test_nights_final.py",
        TESTS_DIR / "booking" / "test_nights_handling.py",
        TESTS_DIR / "booking" / "test_sheet_name.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_integration_tests():
    """Run integration tests (multi-component)"""
    print("\n🔗 RUNNING INTEGRATION TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "integration" / "test_phase_completion.py",
        TESTS_DIR / "integration" / "test_production_readiness.py",
        TESTS_DIR / "integration" / "test_no_duplicate_tasks.py",
        TESTS_DIR / "integration" / "test_agent_validation.py",
        TESTS_DIR / "integration" / "test_combined_behavior.py",
        TESTS_DIR / "integration" / "test_comprehensive_integration.py",
        TESTS_DIR / "integration" / "test_final_validation.py",
        TESTS_DIR / "integration" / "verify_phases.py",
        TESTS_DIR / "integration" / "verify_production_readiness_new.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_production_tests():
    """Run production readiness tests"""
    print("\n🏭 RUNNING PRODUCTION TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "production" / "test_idempotence_constraints.py",
        TESTS_DIR / "production" / "test_production_readiness.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_ui_tests():
    """Run UI and user interface tests"""
    print("\n🎨 RUNNING UI TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "ui" / "test_button_fix_verification.py",
        TESTS_DIR / "ui" / "test_button_functionality_analysis.py",
        TESTS_DIR / "ui" / "test_button_timing_analysis.py",
        TESTS_DIR / "ui" / "test_file_cleanup_ui.py",
        TESTS_DIR / "ui" / "test_nav_visibility.py",
        TESTS_DIR / "ui" / "test_notifications_widget.py",
        TESTS_DIR / "ui" / "test_password_descriptions.py",
        TESTS_DIR / "ui" / "test_password_field_configuration.py",
        TESTS_DIR / "ui" / "test_timing_fix_verification.py",
        TESTS_DIR / "ui" / "test_ui_selector_fix.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_cloudinary_tests():
    """Run Cloudinary integration tests"""
    print("\n☁️ RUNNING CLOUDINARY TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "cloudinary" / "test_cloudinary_config.py",
        TESTS_DIR / "cloudinary" / "test_cloudinary_integration.py",
        TESTS_DIR / "cloudinary" / "debug_cloudinary_auth.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, "-m", "pytest", str(test_file), "-v"], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def main():
    """Main test runner"""
    print("🧪 ARISTAY PROJECT COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"🐍 Python: {get_python_executable()}")
    print(f"📊 Tests Directory: {TESTS_DIR}")
    
    if not BACKEND_DIR.exists():
        print(f"❌ Backend directory not found: {BACKEND_DIR}")
        sys.exit(1)
    
    if not TESTS_DIR.exists():
        print(f"❌ Tests directory not found: {TESTS_DIR}")
        sys.exit(1)
    
    # Track results
    results = {
        "unit": False,
        "api": False,
        "security": False,
        "booking": False,
        "integration": False,
        "production": False,
        "ui": False,
        "cloudinary": False
    }
    
    # Run test suites based on arguments
    if "--unit" in sys.argv or "--all" in sys.argv:
        results["unit"] = run_unit_tests()
    
    if "--api" in sys.argv or "--all" in sys.argv:
        results["api"] = run_api_tests()
    
    if "--security" in sys.argv or "--all" in sys.argv:
        results["security"] = run_security_tests()
    
    if "--booking" in sys.argv or "--all" in sys.argv:
        results["booking"] = run_booking_tests()
    
    if "--integration" in sys.argv or "--all" in sys.argv:
        results["integration"] = run_integration_tests()
    
    if "--production" in sys.argv or "--all" in sys.argv:
        results["production"] = run_production_tests()
    
    if "--ui" in sys.argv or "--all" in sys.argv:
        results["ui"] = run_ui_tests()
    
    if "--cloudinary" in sys.argv or "--all" in sys.argv:
        results["cloudinary"] = run_cloudinary_tests()
    
    # If no specific test type requested, run all
    if not any(arg in sys.argv for arg in ["--unit", "--api", "--security", "--booking", "--integration", "--production", "--ui", "--cloudinary", "--all"]):
        results["unit"] = run_unit_tests()
        results["api"] = run_api_tests()
        results["security"] = run_security_tests()
        results["booking"] = run_booking_tests()
        results["integration"] = run_integration_tests()
        results["production"] = run_production_tests()
        results["ui"] = run_ui_tests()
        results["cloudinary"] = run_cloudinary_tests()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total_run = 0
    total_passed = 0
    
    for test_type, passed in results.items():
        if test_type in ["unit", "api", "security", "booking", "integration", "production", "ui", "cloudinary"]:
            total_run += 1
            if passed:
                total_passed += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            print(f"{test_type.upper():<12}: {status}")
    
    print("-" * 70)
    print(f"OVERALL: {total_passed}/{total_run} test suites passed")
    
    if total_passed == total_run:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    if "--help" in sys.argv:
        print("""
Aristay Comprehensive Test Runner

Usage:
    python run_tests_comprehensive.py [options]

Options:
    --all           Run all test suites (default)
    --unit          Run only unit tests
    --api           Run only API tests
    --security      Run only security tests
    --booking       Run only booking tests
    --integration   Run only integration tests
    --production    Run only production tests
    --ui            Run only UI tests
    --cloudinary    Run only Cloudinary tests
    --help          Show this help message

Examples:
    python run_tests_comprehensive.py                    # Run all tests
    python run_tests_comprehensive.py --api              # Run only API tests
    python run_tests_comprehensive.py --security         # Run only security tests
    python run_tests_comprehensive.py --unit --api       # Run unit and API tests
""")
        sys.exit(0)
    
    main()
