#!/usr/bin/env python3
"""
UI Selector Fix Verification Script
Verifies that the JavaScript UI update function uses correct element selectors
"""

import re
import sys
from pathlib import Path

# Add backend to Python path for imports
backend_path = Path(__file__).parent.parent.parent / "aristay_backend"
sys.path.insert(0, str(backend_path))

def verify_ui_selector_fix():
    """Verify that the updateTaskStatusUI function uses correct selectors"""
    
    template_path = backend_path / "api" / "templates" / "staff" / "task_detail.html"
    
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return False
        
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Analyzing UI selector fix...")
    print("=" * 50)
    
    # Check button HTML structure
    print("1. Checking button HTML structure:")
    start_button_pattern = r'class="btn-action start-task"'
    complete_button_pattern = r'class="btn-action complete-task"'
    
    start_matches = re.findall(start_button_pattern, content)
    complete_matches = re.findall(complete_button_pattern, content)
    
    print(f"   ✅ Start buttons found: {len(start_matches)}")
    print(f"   ✅ Complete buttons found: {len(complete_matches)}")
    
    # Check JavaScript selector usage
    print("\n2. Checking JavaScript selectors:")
    
    # Old problematic patterns (should NOT exist)
    old_start_pattern = r"getElementById\(['\"]startTaskBtn['\"]\)"
    old_complete_pattern = r"getElementById\(['\"]completeTaskBtn['\"]\)"
    
    old_start_matches = re.findall(old_start_pattern, content)
    old_complete_matches = re.findall(old_complete_pattern, content)
    
    if old_start_matches or old_complete_matches:
        print(f"   ❌ Old selectors still present!")
        print(f"      - startTaskBtn references: {len(old_start_matches)}")
        print(f"      - completeTaskBtn references: {len(old_complete_matches)}")
        return False
    
    # New correct patterns (should exist)
    new_start_pattern = r"querySelector\(['\"]\.btn-action\.start-task['\"]\)"
    new_complete_pattern = r"querySelector\(['\"]\.btn-action\.complete-task['\"]\)"
    
    new_start_matches = re.findall(new_start_pattern, content)
    new_complete_matches = re.findall(new_complete_pattern, content)
    
    print(f"   ✅ New start selectors: {len(new_start_matches)}")
    print(f"   ✅ New complete selectors: {len(new_complete_matches)}")
    
    # Check for debugging logs
    print("\n3. Checking debug logging:")
    debug_patterns = [
        r"console\.log\(['\"]🔄 Updating UI",
        r"console\.log\(['\"]✅ Status badge updated",
        r"console\.log\(['\"]🔍 Buttons found",
        r"console\.log\(['\"]✅ UI update complete"
    ]
    
    debug_count = 0
    for pattern in debug_patterns:
        matches = re.findall(pattern, content)
        debug_count += len(matches)
        print(f"   📝 Debug log found: {len(matches) > 0}")
    
    # Check for visual feedback improvements
    print("\n4. Checking visual feedback:")
    opacity_pattern = r"\.style\.opacity"
    opacity_matches = re.findall(opacity_pattern, content)
    print(f"   ✨ Opacity styling: {len(opacity_matches)} instances")
    
    # Check for status replacement fix
    status_replace_pattern = r"status-\$\{data\.status\.replace\("
    status_matches = re.findall(status_replace_pattern, content)
    print(f"   🔧 Status replacement fix: {len(status_matches) > 0}")
    
    print("\n" + "=" * 50)
    
    # Final assessment
    success_criteria = [
        len(start_matches) > 0,  # Buttons exist with correct classes
        len(complete_matches) > 0,
        len(old_start_matches) == 0,  # Old selectors removed
        len(old_complete_matches) == 0,
        len(new_start_matches) > 0,  # New selectors present
        len(new_complete_matches) > 0,
        debug_count > 0,  # Debug logging added
        len(opacity_matches) > 0  # Visual feedback added
    ]
    
    if all(success_criteria):
        print("🎉 ALL CHECKS PASSED!")
        print("   ✅ Button HTML structure correct")
        print("   ✅ Old problematic selectors removed") 
        print("   ✅ New correct selectors implemented")
        print("   ✅ Debug logging added")
        print("   ✅ Visual feedback enhancements present")
        print("\n💡 The UI selector fix has been successfully implemented!")
        print("   Buttons should now update immediately when clicked.")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print("   Please review the implementation.")
        return False

if __name__ == "__main__":
    print("🔧 UI Selector Fix Verification")
    print("Testing JavaScript element selector corrections")
    print()
    
    success = verify_ui_selector_fix()
    sys.exit(0 if success else 1)
