#!/usr/bin/env python3
"""
Verification script to confirm the timing fix is correctly applied.
"""

import os
import sys
import django

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aristay_backend')
sys.path.append(backend_path)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def verify_timing_fix():
    """Verify that the timing fix is correctly applied"""
    
    print("🔍 VERIFICATION: Timing Fix Applied")
    print("=" * 45)
    
    # Read the template file
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aristay_backend', 'api', 'templates', 'staff', 'task_detail.html')
    
    try:
        with open(template_path, 'r') as f:
            lines = f.readlines()
        
        # Find key execution points
        execution_points = {}
        function_definitions = []
        
        for i, line in enumerate(lines, 1):
            if "document.addEventListener('DOMContentLoaded'" in line:
                execution_points['DOMContentLoaded'] = i
            elif "window.startTask = function" in line:
                function_definitions.append(('startTask', i))
            elif "window.completeTask = function" in line:
                function_definitions.append(('completeTask', i))
            elif "window.addNote = function" in line:
                function_definitions.append(('addNote', i))
            elif "window.shareTask = function" in line:
                function_definitions.append(('shareTask', i))
        
        print(f"\n📋 EXECUTION ORDER CHECK:")
        print("-" * 25)
        
        dom_loaded_line = execution_points.get('DOMContentLoaded', 0)
        print(f"DOMContentLoaded event: Line {dom_loaded_line}")
        
        print(f"\nFunction definitions:")
        for func_name, line_num in function_definitions:
            print(f"  window.{func_name}: Line {line_num}")
        
        # Check if timing is now correct
        timing_correct = True
        issues = []
        
        for func_name, line_num in function_definitions:
            if line_num > dom_loaded_line:
                timing_correct = False
                issues.append(f"window.{func_name} defined AFTER DOMContentLoaded (Line {line_num} > {dom_loaded_line})")
        
        print(f"\n🎯 TIMING ANALYSIS:")
        print("-" * 20)
        
        if timing_correct:
            print("✅ TIMING FIX SUCCESSFUL!")
            print("   - All function definitions come BEFORE DOMContentLoaded")
            print("   - Event listeners will be able to reference the functions")
            print("   - Buttons should now work correctly")
        else:
            print("❌ TIMING ISSUES REMAIN:")
            for issue in issues:
                print(f"   - {issue}")
        
        # Check for duplicate definitions
        function_counts = {}
        for func_name, line_num in function_definitions:
            if func_name in function_counts:
                function_counts[func_name].append(line_num)
            else:
                function_counts[func_name] = [line_num]
        
        print(f"\n🔄 DUPLICATE CHECK:")
        print("-" * 18)
        
        duplicates_found = False
        for func_name, line_nums in function_counts.items():
            if len(line_nums) > 1:
                duplicates_found = True
                print(f"❌ window.{func_name} defined {len(line_nums)} times: Lines {line_nums}")
            else:
                print(f"✅ window.{func_name}: Single definition at Line {line_nums[0]}")
        
        if not duplicates_found:
            print("✅ No duplicate function definitions found")
        
        return timing_correct and not duplicates_found
        
    except Exception as e:
        print(f"Error analyzing template: {str(e)}")
        return False

def main():
    """Run verification"""
    
    try:
        print("🧪 TIMING FIX VERIFICATION")
        print("=" * 50)
        
        success = verify_timing_fix()
        
        if success:
            print(f"\n🎉 COMPLETE SUCCESS!")
            print("=" * 25)
            print("✅ Functions defined before DOMContentLoaded")
            print("✅ No duplicate function definitions")
            print("✅ Timing issue resolved")
            print("✅ Buttons should now work!")
            print("")
            print("🧪 MANUAL TEST:")
            print("   1. Start Django server: python manage.py runserver")
            print("   2. Visit: http://localhost:8000/api/staff/tasks/2/")
            print("   3. Open browser console and type: window.startTask")
            print("   4. Should show: function(taskId) { ... }")
            print("   5. Click 'Start Task' button - should work!")
            
        else:
            print(f"\n❌ FIX INCOMPLETE!")
            print("   - Timing or duplicate issues remain")
            print("   - Manual correction needed")
            
        return success
        
    except Exception as e:
        print(f"\n💥 ERROR during verification: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
