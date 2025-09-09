#!/usr/bin/env python3
"""
Advanced diagnostic to test the ACTUAL execution order and timing issue.
This will create a comprehensive analysis of the JavaScript execution flow.
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

def analyze_execution_order():
    """Analyze the JavaScript execution order in task_detail.html"""
    
    print("🔍 ADVANCED ANALYSIS: JavaScript Execution Order")
    print("=" * 60)
    
    # Read the template file
    template_path = '/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend/api/templates/staff/task_detail.html'
    
    try:
        with open(template_path, 'r') as f:
            lines = f.readlines()
        
        # Find key execution points
        execution_points = {}
        
        for i, line in enumerate(lines, 1):
            if "document.addEventListener('DOMContentLoaded'" in line:
                execution_points['DOMContentLoaded'] = i
            elif "function initializeTaskActions()" in line:
                execution_points['initializeTaskActions_def'] = i
            elif "initializeTaskActions();" in line:
                execution_points['initializeTaskActions_call'] = i
            elif "window.startTask = function" in line:
                execution_points['window_startTask_def'] = i
            elif "window.completeTask = function" in line:
                execution_points['window_completeTask_def'] = i
            elif "window.addNote = function" in line:
                execution_points['window_addNote_def'] = i
            elif "addEventListener('click', () => window.startTask" in line:
                execution_points['startTask_listener'] = i
        
        print("\n📋 EXECUTION ORDER ANALYSIS:")
        print("-" * 40)
        
        # Sort by line number to see actual execution order
        sorted_points = sorted(execution_points.items(), key=lambda x: x[1])
        
        for point, line_num in sorted_points:
            print(f"Line {line_num:4d}: {point}")
        
        # Check if timing issue exists
        print("\n🚨 TIMING ISSUE ANALYSIS:")
        print("-" * 30)
        
        dom_loaded = execution_points.get('DOMContentLoaded', 0)
        init_call = execution_points.get('initializeTaskActions_call', 0)
        start_task_def = execution_points.get('window_startTask_def', 0)
        start_listener = execution_points.get('startTask_listener', 0)
        
        print(f"DOMContentLoaded event: Line {dom_loaded}")
        print(f"initializeTaskActions() call: Line {init_call}")
        print(f"Event listener attachment: Line {start_listener}")
        print(f"window.startTask definition: Line {start_task_def}")
        
        # Check the critical timing issue
        if dom_loaded < start_task_def:
            print(f"\n❌ CRITICAL TIMING ISSUE CONFIRMED:")
            print(f"   - DOMContentLoaded (Line {dom_loaded}) runs BEFORE window.startTask is defined (Line {start_task_def})")
            print(f"   - This means event listeners try to reference undefined functions!")
            timing_issue = True
        else:
            print(f"\n✅ TIMING IS CORRECT:")
            print(f"   - Functions are defined before DOMContentLoaded")
            timing_issue = False
        
        # Detailed flow analysis
        print(f"\n🔄 ACTUAL EXECUTION FLOW:")
        print(f"1. Browser loads page and parses JavaScript")
        print(f"2. Function definitions are parsed (but not executed until called)")
        print(f"3. DOMContentLoaded event fires (Line {dom_loaded})")
        print(f"4. initializeTaskActions() is called (Line {init_call})")
        print(f"5. Event listeners try to reference window.startTask")
        
        if timing_issue:
            print(f"6. ❌ BUT window.startTask is not defined yet (defined at Line {start_task_def})")
            print(f"7. ❌ Event listeners reference undefined functions → buttons don't work")
        else:
            print(f"6. ✅ window.startTask is already defined → buttons should work")
        
        return timing_issue
        
    except Exception as e:
        print(f"Error analyzing template: {str(e)}")
        return None

def check_agent_response_accuracy():
    """Check if the agent's response is accurate"""
    
    print(f"\n🧪 AGENT RESPONSE VERIFICATION:")
    print("=" * 40)
    
    timing_issue = analyze_execution_order()
    
    if timing_issue is True:
        print(f"\n✅ AGENT RESPONSE: CORRECT")
        print("   - Agent correctly identified timing issue")
        print("   - Functions ARE defined after DOMContentLoaded")
        print("   - Moving function definitions before DOMContentLoaded IS the right fix")
        return True
        
    elif timing_issue is False:
        print(f"\n❌ AGENT RESPONSE: INCORRECT")
        print("   - Agent incorrectly claimed timing issue")
        print("   - Functions are already defined before DOMContentLoaded")
        print("   - The timing issue doesn't exist")
        return False
        
    else:
        print(f"\n❓ AGENT RESPONSE: INDETERMINATE")
        print("   - Unable to verify due to analysis error")
        return None

def provide_correct_solution():
    """Provide the actual correct solution based on analysis"""
    
    timing_issue = analyze_execution_order()
    
    print(f"\n🔧 CORRECT SOLUTION:")
    print("=" * 20)
    
    if timing_issue is True:
        print("✅ MOVE FUNCTION DEFINITIONS (Agent's solution is correct)")
        print("   The functions need to be moved before DOMContentLoaded")
        
    elif timing_issue is False:
        print("🔍 DIFFERENT ISSUE - Need deeper debugging")
        print("   The timing is correct, so the issue is something else:")
        print("   - Check if buttons are actually disabled")
        print("   - Check for JavaScript errors in console")
        print("   - Check if DOM elements exist when event listeners attach")
        print("   - Check if CSRF token is available")
        print("   - Check if API endpoint is accessible")
        
    else:
        print("❓ UNABLE TO DETERMINE - Manual debugging needed")

def main():
    """Run the advanced analysis"""
    
    try:
        print("🚀 ADVANCED BUTTON FUNCTIONALITY ANALYSIS")
        print("=" * 70)
        
        # Run the comprehensive analysis
        is_agent_correct = check_agent_response_accuracy()
        provide_correct_solution()
        
        print(f"\n🎯 FINAL VERDICT:")
        print("=" * 15)
        
        if is_agent_correct is True:
            print("✅ THE AGENT'S RESPONSE IS CORRECT")
            print("   - Timing issue confirmed")
            print("   - Solution (move functions) is appropriate")
            print("   - My previous fix was insufficient")
            
        elif is_agent_correct is False:
            print("❌ THE AGENT'S RESPONSE IS INCORRECT")
            print("   - No timing issue found")
            print("   - My previous fix should have worked")
            print("   - Need different debugging approach")
            
        else:
            print("❓ UNABLE TO VERIFY AGENT'S RESPONSE")
            print("   - Analysis inconclusive")
            
        return is_agent_correct
        
    except Exception as e:
        print(f"\n💥 ERROR during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    result = main()
    if result is True:
        print("\n→ RECOMMENDATION: Apply the agent's suggested fix")
    elif result is False:
        print("\n→ RECOMMENDATION: Investigate other causes")
    else:
        print("\n→ RECOMMENDATION: Manual debugging required")
