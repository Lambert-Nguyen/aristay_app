#!/usr/bin/env python3
"""
Refactor task_detail.html - Phase 2 Week 4
Replaces inline HTML sections with component includes and inline JS with modules
"""

def refactor_task_detail():
    template_path = "aristay_backend/api/templates/staff/task_detail.html"
    
    with open(template_path, 'r') as f:
        lines = f.readlines()
    
    # Find key line numbers
    content_start = None
    content_end = None
    extra_js_start = None
    extra_js_end = None
    extra_css_start = None
    
    for i, line in enumerate(lines):
        if '{% block content %}' in line:
            content_start = i
        elif content_start is not None and content_end is None and '{% endblock %}' in line:
            content_end = i
        elif '{% block extra_js %}' in line:
            extra_js_start = i
        elif extra_js_start is not None and extra_js_end is None and '{% endblock %}' in line:
            extra_js_end = i
        elif '{% block extra_css %}' in line:
            extra_css_start = i
            break
    
    print(f"content: {content_start}-{content_end}")
    print(f"extra_js: {extra_js_start}-{extra_js_end}")
    print(f"extra_css: {extra_css_start}")
    
    # Read content block
    content_lines = lines[content_start+1:content_end]
    
    # Find component boundaries in content
    timer_start = None
    nav_start = None
    progress_start = None
    checklist_start = None
    
    for i, line in enumerate(content_lines):
        if '<!-- Task Timer -->' in line:
            timer_start = i
        elif '<!-- Navigation -->' in line:
            nav_start = i
        elif '<!-- Task Progress Overview -->' in line:
            progress_start = i
        elif '<!-- Checklist Sections -->' in line:
            checklist_start = i
    
    print(f"Components in content: timer={timer_start}, nav={nav_start}, progress={progress_start}, checklist={checklist_start}")
    
    # Build new content with component includes
    new_content = []
    
    # Add everything before timer
    new_content.extend(content_lines[:timer_start])
    
    # Replace timer section with include
    new_content.append("                {# Component: Task Timer #}\n")
    new_content.append("                {% include \"staff/components/task_timer.html\" %}\n")
    new_content.append("\n")
    
    # Replace navigation section with include
    new_content.append("                {# Component: Task Navigation #}\n")
    new_content.append("                {% include \"staff/components/task_navigation.html\" %}\n")
    
    # Find end of navigation (before "    </div>" that closes task-actions-section)
    nav_end = None
    for i in range(nav_start, len(content_lines)):
        if i > nav_start + 15 and '            </div>' in content_lines[i] and '</div>' in content_lines[i+1] and '</div>' in content_lines[i+2]:
            nav_end = i + 3
            break
    
    # Add closing divs
    new_content.extend(content_lines[nav_end-3:progress_start])
    
    # Replace progress section with include
    new_content.append("\n    {# Component: Task Progress Overview #}\n")
    new_content.append("    {% include \"staff/components/task_progress.html\" %}\n")
    new_content.append("\n")
    
    # Replace checklist section with include  
    new_content.append("    {# Component: Task Checklist #}\n")
    new_content.append("    {% include \"staff/components/task_checklist.html\" %}\n")
    
    # Find end of checklist (everything else before endblock)
    checklist_end = None
    for i in range(checklist_start, len(content_lines)):
        if '<!-- Task Notes/Comments -->' in content_lines[i]:
            checklist_end = i
            break
    
    # Add remaining content (notes section etc)
    new_content.extend(content_lines[checklist_end:])
    
    # Build new file
    new_lines = []
    new_lines.extend(lines[:content_start+1])  # Everything before content block
    new_lines.extend(new_content)  # New content with includes
    new_lines.append("{% endblock %}\n\n")
    
    # New extra_js block with module imports
    new_lines.append("{% block extra_js %}\n")
    new_lines.append("{% load static %}\n")
    new_lines.append("{# Load modular JavaScript - replaces 1,400+ lines of inline code #}\n")
    new_lines.append("<script type=\"module\" src=\"{% static 'js/pages/task-detail.js' %}\"></script>\n\n")
    new_lines.append("{# Task data for JavaScript modules #}\n")
    new_lines.append("<script id=\"taskData\" type=\"application/json\">\n")
    new_lines.append("{\n")
    new_lines.append("  \"taskId\": {{ task.id }},\n")
    new_lines.append("  \"taskStatus\": \"{{ task.status }}\",\n")
    new_lines.append("  \"canEdit\": {{ can_edit|yesno:\"true,false\" }},\n")
    new_lines.append("  \"hasChecklist\": {{ checklist|yesno:\"true,false\" }}\n")
    new_lines.append("}\n")
    new_lines.append("</script>\n")
    new_lines.append("{% endblock %}\n\n")
    
    # Add extra_css block (keep original CSS)
    new_lines.extend(lines[extra_css_start:])
    
    # Write new file
    with open(template_path, 'w') as f:
        f.writelines(new_lines)
    
    # Calculate stats
    original_lines = len(lines)
    new_file_lines = len(new_lines)
    removed = original_lines - new_file_lines
    
    print(f"\n✅ Refactoring complete!")
    print(f"Original: {original_lines} lines")
    print(f"New: {new_file_lines} lines")
    print(f"Removed: {removed} lines ({removed/original_lines*100:.1f}%)")

if __name__ == "__main__":
    refactor_task_detail()
