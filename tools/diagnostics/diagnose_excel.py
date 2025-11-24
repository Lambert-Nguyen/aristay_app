#!/usr/bin/env python3
"""
Quick test script to diagnose Excel import issues
"""

import sys
import pandas as pd

def test_excel_file(filepath):
    """Test reading an Excel file with pandas and openpyxl"""
    print(f"Testing Excel file: {filepath}")
    
    try:
        # Try reading with pandas/openpyxl (default)
        print("Attempting to read with pandas and openpyxl...")
        df = pd.read_excel(filepath, engine='openpyxl')
        print(f"✅ Success! Read {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Try different sheet names
        print("\nChecking available sheets...")
        with pd.ExcelFile(filepath, engine='openpyxl') as xls:
            print(f"Available sheets: {xls.sheet_names}")
            
            # Try reading specific sheet
            for sheet_name in ['Cleaning schedule', 'Sheet1']:
                if sheet_name in xls.sheet_names:
                    print(f"\nTrying sheet '{sheet_name}'...")
                    df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')
                    print(f"✅ Sheet '{sheet_name}': {len(df)} rows")
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try alternative engines
        print("\nTrying alternative engines...")
        
        try:
            # Try with xlrd
            print("Trying xlrd engine...")
            df = pd.read_excel(filepath, engine='xlrd')
            print(f"✅ Success with xlrd! Read {len(df)} rows")
            return True
        except Exception as e2:
            print(f"❌ xlrd failed: {e2}")
        
        return False

if __name__ == "__main__":
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    excel_file = project_root / "docs" / "requirements" / "Cleaning_schedule_1.xlsx"

    if excel_file.exists():
        test_excel_file(str(excel_file))
    else:
        print(f"❌ Excel file not found at: {excel_file}")
        print("Skipping test.")
