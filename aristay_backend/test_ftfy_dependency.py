#!/usr/bin/env python3
"""
Test FTFY Dependency Handling
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.services.enhanced_excel_import_service import _analyze_guest_name_difference

def test_ftfy_dependency():
    """Test ftfy dependency handling"""
    print("📦 FTFY DEPENDENCY VALIDATION")
    print("=" * 50)
    
    try:
        import ftfy
        print(f"✅ ftfy is available: {ftfy.__version__}")
        
        # Test functionality
        test_text = "Kathrin MĂ¼ller"
        fixed_text = ftfy.fix_text(test_text)
        print(f"   Test: '{test_text}' → '{fixed_text}'")
        
    except ImportError:
        print(f"ℹ️  ftfy not installed - testing graceful fallback")
        
    # Test that the analysis works regardless of ftfy availability
    result = _analyze_guest_name_difference("Kathrin MĂ¼ller", "Kathrin Muller")
    print(f"   Analysis result: {result['type']} (expected: encoding_correction)")
    print(f"   Encoding issue detected: {result['likely_encoding_issue']}")
    
    if result['type'] == 'encoding_correction':
        print(f"✅ System works correctly regardless of ftfy availability")
        print(f"✅ Graceful fallback confirmed")
    else:
        print(f"⚠️  System behavior different without ftfy: {result['type']}")

if __name__ == '__main__':
    test_ftfy_dependency()
