#!/usr/bin/env python3
"""
Centralized Test Runner for Aristay Project
Runs all tests in the organized test structure
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

def run_production_tests():
    """Run production hardening tests"""
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
            if not run_command([python_exe, str(test_file)], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 RUNNING INTEGRATION TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    test_files = [
        TESTS_DIR / "integration" / "test_phase_completion.py",
        TESTS_DIR / "integration" / "test_production_readiness.py",
        TESTS_DIR / "integration" / "test_no_duplicate_tasks.py"
    ]
    
    success = True
    for test_file in test_files:
        if test_file.exists():
            if not run_command([python_exe, str(test_file)], cwd=BACKEND_DIR):
                success = False
        else:
            print(f"⚠️  Test file not found: {test_file}")
    
    return success

def run_django_tests():
    """Run Django's built-in tests"""
    print("\n🐍 RUNNING DJANGO TESTS")
    print("=" * 50)
    
    python_exe = get_python_executable()
    return run_command([python_exe, "manage.py", "test"], cwd=BACKEND_DIR)

def main():
    """Main test runner"""
    print("🧪 ARISTAY PROJECT TEST SUITE")
    print("=" * 60)
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
        "production": False,
        "integration": False,
        "django": False
    }
    
    # Run test suites
    if "--production" in sys.argv or "--all" in sys.argv:
        results["production"] = run_production_tests()
    
    if "--integration" in sys.argv or "--all" in sys.argv:
        results["integration"] = run_integration_tests()
    
    if "--django" in sys.argv or "--all" in sys.argv:
        results["django"] = run_django_tests()
    
    # If no specific test type requested, run all
    if not any(arg in sys.argv for arg in ["--production", "--integration", "--django", "--all"]):
        results["production"] = run_production_tests()
        results["integration"] = run_integration_tests() 
        results["django"] = run_django_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_run = 0
    total_passed = 0
    
    for test_type, passed in results.items():
        if test_type in ["production", "integration", "django"]:
            total_run += 1
            if passed:
                total_passed += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            print(f"{test_type.upper():<12}: {status}")
    
    print("-" * 60)
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
Aristay Test Runner

Usage:
    python run_tests.py [options]

Options:
    --all           Run all test suites (default)
    --production    Run only production hardening tests
    --integration   Run only integration tests  
    --django        Run only Django built-in tests
    --help          Show this help message

Examples:
    python run_tests.py                 # Run all tests
    python run_tests.py --production    # Run only production tests
    python run_tests.py --integration   # Run only integration tests
""")
        sys.exit(0)
    
    main()
