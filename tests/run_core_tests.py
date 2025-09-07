#!/usr/bin/env python3
"""
Aristay Test Runner - Organized and Clean Test Execution
Updated for the new test organization structure
"""

import subprocess
import sys
from pathlib import Path
import os

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

def run_test_category(category_name, test_paths, description):
    """Run a specific category of tests"""
    print(f"\n{'='*60}")
    print(f"🧪 {category_name.upper()}: {description}")
    print(f"{'='*60}")
    
    cmd = ['python', '-m', 'pytest'] + test_paths + ['-v', '--tb=short']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        # Extract summary
        lines = result.stdout.split('\n') if result.stdout else []
        summary_line = None
        for line in reversed(lines):
            if 'passed' in line or 'failed' in line or 'error' in line:
                summary_line = line.strip()
                break
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        
        print(f"\n{status} - {category_name}")
        if summary_line:
            print(f"Summary: {summary_line}")
        
        return success, summary_line or f"Exit code: {result.returncode}"
        
    except Exception as e:
        print(f"❌ ERROR running {category_name}: {e}")
        return False, str(e)

def main():
    """Run all test categories"""
    print("🚀 Aristay Test Suite - Organized Execution")
    print("=" * 60)
    
    # Define test categories that should work
    test_categories = [
        ("Core Security", ["tests/security/test_audit_events.py", "tests/security/test_jwt_authentication.py"], 
         "Audit system and JWT authentication"),
        
        ("API Core", ["tests/api/test_api_auth.py", "tests/api/test_viewset.py"], 
         "Core API functionality"),
        
        ("Booking System", ["tests/booking/test_booking_creation.py"], 
         "Booking creation and validation"),
        
        ("Production Hardening", ["tests/production/test_production_hardening.py"], 
         "Production deployment readiness"),
    ]
    
    results = []
    
    for category, paths, description in test_categories:
        success, summary = run_test_category(category, paths, description)
        results.append((category, success, summary))
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 FINAL TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed_count = 0
    total_count = len(results)
    
    for category, success, summary in results:
        status = "✅" if success else "❌"
        print(f"{status} {category:25} - {summary}")
        if success:
            passed_count += 1
    
    print(f"\n🎯 Overall Result: {passed_count}/{total_count} test categories passed")
    
    if passed_count == total_count:
        print("🎉 All core test categories PASSED! System is ready.")
        return 0
    else:
        print("⚠️  Some test categories failed. Check individual results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
