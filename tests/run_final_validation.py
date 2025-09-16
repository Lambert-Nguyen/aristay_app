#!/usr/bin/env python3
"""
Final validation runner - demonstrates "all green" test status.
Runs all critical tests to validate production readiness.
"""

import os, sys, subprocess
from pathlib import Path

# Project root: .../aristay_app
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "aristay_backend"

def get_python_executable():
    """Get the appropriate Python executable for the current environment"""
    # Check if we're in CI environment
    if os.getenv('GITHUB_ACTIONS') or os.getenv('CI'):
        return 'python'  # Use system python in CI
    
    # Check for local virtual environment
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    
    # Fallback to system python
    return 'python'

PYTHON_EXE = get_python_executable()

def run_test(test_name, test_path):
    """Run a test and return True if it passes"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}")
    print(f"{'='*60}")
    
    try:
        # Use pytest to run the test with proper database setup
        result = subprocess.run([
            PYTHON_EXE, "-m", "pytest", str(test_path), "-v", "--tb=short"
        ], capture_output=False, text=True, cwd=str(ROOT))
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status}: {test_name}")
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {test_name} - {e}")
        return False

def main():
    print("🚀 FINAL VALIDATION: All Green Test Status")
    print("="*80)
    
    tests = [
        ("Production Hardening", "tests/production/test_production_readiness.py"),
        ("Phase 6 Integration", "tests/integration/test_final_validation.py"),
        ("Production Readiness", "tests/integration/verify_production_readiness_new.py"),
    ]
    
    passed = 0
    total = len(tests)
    results = []
    
    for test_name, test_path in tests:
        ok = run_test(test_name, test_path)
        results.append((test_name, ok))
        if ok:
            passed += 1
    
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    
    for i, (name, ok) in enumerate(results, 1):
        mark = "✅" if ok else "❌"
        print(f"{mark} {i}. {name}")
    
    print(f"\n🎯 Overall Status: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🌟 CONGRATULATIONS! 🌟")
        print("🎉 ALL GREEN - Production system fully validated!")
        print("✅ Production hardening complete")
        print("✅ Integration tests passing")  
        print("✅ Production readiness verified")
        print("\n🚀 System is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failing - review output above")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
