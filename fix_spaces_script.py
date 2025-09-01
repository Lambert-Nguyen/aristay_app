#!/usr/bin/env python3
"""
System-wide space fix script for AriStay Django project
Fixes systematic issue where spaces have been inserted into string literals
"""

import os
import re
import glob
from pathlib import Path

def fix_spaces_in_file(file_path):
    """Fix space issues in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix patterns with spaces that should not have them
        fixes = [
            # Template paths
            (r'"(\w+)\s+/\s+(\w+)\.html"', r'"\1/\2.html"'),
            (r'"(\w+)\s+/\s+(\w+)\s+/\s+(\w+)\.html"', r'"\1/\2/\3.html"'),
            (r'"(\w+)\s+/\s+(\w+)\s+/\s+(\w+)\s+/\s+(\w+)\.html"', r'"\1/\2/\3/\4.html"'),
            
            # URL paths  
            (r'"/(\w+)\s+/\s+(\w+)/"', r'"/\1/\2/"'),
            (r'"/(\w+)\s+/\s+(\w+)\s+/\s+(\w+)/"', r'"/\1/\2/\3/"'),
            (r'"/(\w+)\s+/\s+(\w+)\s+/\s+(\w+)\s+/\s+(\w+)/"', r'"/\1/\2/\3/\4/"'),
            
            # API paths
            (r'"/api\s+/\s+(\w+)/"', r'"/api/\1/"'),
            (r'"/api\s+/\s+(\w+)\s+/\s+(\w+)/"', r'"/api/\1/\2/"'),
            (r'"/api\s+/\s+(\w+)\s+/\s+(\w+)\s+/\s+(\w+)/"', r'"/api/\1/\2/\3/"'),
            
            # Admin paths
            (r'"/admin\s+/\s+(\w+)/"', r'"/admin/\1/"'),
            (r'"/admin\s+/\s+(\w+)\s+/\s+(\w+)/"', r'"/admin/\1/\2/"'),
            
            # Content types
            (r'"application\s+/\s+json"', r'"application/json"'),
            (r'"text\s+/\s+html"', r'"text/html"'),
            (r'"text\s+/\s+plain"', r'"text/plain"'),
            
            # Timezone identifiers
            (r'"America\s+/\s+New_York"', r'"America/New_York"'),
            (r'"America\s+/\s+Los_Angeles"', r'"America/Los_Angeles"'),
            (r'"America\s+/\s+Chicago"', r'"America/Chicago"'),
            (r'"America\s+/\s+Denver"', r'"America/Denver"'),
            (r'"America\s+/\s+Phoenix"', r'"America/Phoenix"'),
            (r'"America\s+/\s+Anchorage"', r'"America/Anchorage"'),
            (r'"Pacific\s+/\s+Honolulu"', r'"Pacific/Honolulu"'),
            (r'"Asia\s+/\s+Ho_Chi_Minh"', r'"Asia/Ho_Chi_Minh"'),
            (r'"Europe\s+/\s+London"', r'"Europe/London"'),
            
            # File paths in strings
            (r'"(\w+)\s+/\s+(\w+)"', r'"\1/\2"'),
            (r'"/(\w+)\s+/\s+(\w+)"', r'"/\1/\2"'),
            
            # Shebang lines
            (r'#!/usr\s+/\s+bin\s+/\s+env\s+python3?', r'#!/usr/bin/env python3'),
            
            # HTTP status patterns  
            (r'startswith\("/admin/"\)\s+and\s+not\s+request\.path\.startswith\("/admin\s+/\s+login/"\)', 
             r'startswith("/admin/") and not request.path.startswith("/admin/login/")'),
        ]
        
        # Apply fixes
        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content)
        
        # Save if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix spaces system-wide"""
    project_root = Path("/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend")
    
    # File patterns to process
    patterns = [
        "**/*.py",
        "**/*.html", 
        "**/*.js",
        "**/*.css",
    ]
    
    total_files = 0
    fixed_files = 0
    
    print("🔧 Starting system-wide space fix...")
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file():
                total_files += 1
                if fix_spaces_in_file(str(file_path)):
                    fixed_files += 1
                    print(f"✅ Fixed: {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"   Total files processed: {total_files}")
    print(f"   Files fixed: {fixed_files}")
    print(f"   Files unchanged: {total_files - fixed_files}")
    
    if fixed_files > 0:
        print(f"\n✅ Successfully fixed {fixed_files} files!")
        print("🔄 Please restart your Django server to apply changes.")
    else:
        print("\n✅ No files needed fixing.")

if __name__ == "__main__":
    main()
