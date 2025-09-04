#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Guest Name Analysis

Tests all requested scenarios including German ß → ss mapping,
encoding corrections, diacritics, and various edge cases.
"""

import os
import sys
import django
from datetime import datetime, date

# Add the parent directory to the path to import Django modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.services.enhanced_excel_import_service import _analyze_guest_name_difference

def test_name_analysis_scenarios():
    """Test all requested guest name analysis scenarios"""
    
    print("🧪 ENHANCED GUEST NAME ANALYSIS TEST SUITE")
    print("=" * 60)
    
    test_cases = [
        # 1. HMZE8BT5AC scenario - Encoding correction
        {
            'existing': 'Kathrin MĂ¼ller',
            'new': 'Kathrin Muller',
            'expected_type': 'encoding_correction',
            'expected_encoding_issue': True,
            'description': 'HMZE8BT5AC - Classic mojibake encoding fix'
        },
        
        # 2. Diacritics only
        {
            'existing': 'José García',
            'new': 'Jose Garcia',
            'expected_type': 'diacritics_only',
            'expected_encoding_issue': True,
            'description': 'Spanish diacritics removal'
        },
        
        # 3. Curly vs straight apostrophe
        {
            'existing': "O'Connor",  # Curly apostrophe
            'new': "O'Connor",      # Straight apostrophe
            'expected_type': 'diacritics_only',  # Normalization makes them same
            'expected_encoding_issue': True,
            'description': 'Curly vs straight apostrophe'
        },
        
        # 4. German ß → ss mapping
        {
            'existing': 'Müller',
            'new': 'Mußler', 
            'expected_type': 'minor_correction',  # Different after ß→ss normalization
            'expected_encoding_issue': False,
            'description': 'German ß handling test case 1'
        },
        
        # 5. German ß → ss mapping reverse
        {
            'existing': 'Mußler',
            'new': 'Mussler',
            'expected_type': 'diacritics_only',  # Should normalize to same after ß→ss
            'expected_encoding_issue': True,
            'description': 'German ß → ss mapping'
        },
        
        # 6. Significant change
        {
            'existing': 'John Smith',
            'new': 'Jane Doe',
            'expected_type': 'significant_change',
            'expected_encoding_issue': False,
            'description': 'Completely different names'
        },
        
        # 7. Minor typo
        {
            'existing': 'John Smith',
            'new': 'Jon Smith',
            'expected_type': 'minor_correction',
            'expected_encoding_issue': False,
            'description': 'Minor typo correction'
        },
        
        # 8. Missing data
        {
            'existing': 'John Smith',
            'new': '',
            'expected_type': 'missing_data',
            'expected_encoding_issue': False,
            'description': 'Missing new name'
        },
        
        # 9. Additional European characters
        {
            'existing': 'Øystein Ræstad',
            'new': 'Oystein Raestad',
            'expected_type': 'diacritics_only',
            'expected_encoding_issue': True,
            'description': 'Norwegian Ø and æ characters'
        },
        
        # 10. Polish Ł
        {
            'existing': 'Łukasz Nowak',
            'new': 'Lukasz Nowak',
            'expected_type': 'diacritics_only',
            'expected_encoding_issue': True,
            'description': 'Polish Ł character'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['description']}")
        print(f"   Existing: '{case['existing']}'")
        print(f"   New: '{case['new']}'")
        
        try:
            result = _analyze_guest_name_difference(case['existing'], case['new'])
            
            # Check type
            if result['type'] == case['expected_type']:
                print(f"   ✅ Type: {result['type']}")
            else:
                print(f"   ❌ Type: Expected {case['expected_type']}, got {result['type']}")
                failed += 1
                continue
            
            # Check encoding issue flag
            if result['likely_encoding_issue'] == case['expected_encoding_issue']:
                print(f"   ✅ Encoding issue: {result['likely_encoding_issue']}")
            else:
                print(f"   ❌ Encoding issue: Expected {case['expected_encoding_issue']}, got {result['likely_encoding_issue']}")
                failed += 1
                continue
            
            print(f"   📄 Description: {result['description']}")
            passed += 1
            
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {len(test_cases)}")
    
    if failed == 0:
        print("🎉 ALL ENHANCED NAME ANALYSIS TESTS PASSED!")
        return True
    else:
        print(f"⚠️  {failed} tests failed. Please review implementation.")
        return False

def test_edge_cases():
    """Test additional edge cases"""
    print("\n" + "=" * 60)
    print("🔍 TESTING EDGE CASES")
    print("=" * 60)
    
    edge_cases = [
        # Empty strings
        ('', '', 'missing_data'),
        (None, 'John', 'missing_data'),
        ('John', None, 'missing_data'),
        
        # Same names
        ('John Smith', 'John Smith', 'diacritics_only'),
        
        # Case differences only
        ('john smith', 'John Smith', 'diacritics_only'),
        
        # Extra spaces
        ('John  Smith', 'John Smith', 'diacritics_only'),
    ]
    
    for existing, new, expected_type in edge_cases:
        try:
            result = _analyze_guest_name_difference(existing or '', new or '')
            if result['type'] == expected_type:
                print(f"   ✅ '{existing}' vs '{new}' → {result['type']}")
            else:
                print(f"   ❌ '{existing}' vs '{new}' → Expected {expected_type}, got {result['type']}")
        except Exception as e:
            print(f"   💥 ERROR with '{existing}' vs '{new}': {e}")

if __name__ == '__main__':
    success = test_name_analysis_scenarios()
    test_edge_cases()
    
    if success:
        print("\n🚀 ENHANCED NAME ANALYSIS IS READY FOR PRODUCTION!")
    else:
        print("\n⚠️  Please fix failed tests before deployment.")
