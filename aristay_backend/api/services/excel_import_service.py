"""
DEPRECATED SHIM - Excel Import Service

This file is maintained for compatibility but routes to the enhanced implementation.
All new development should use enhanced_excel_import_service.py directly.

GPT Agent Fix: Keep file to avoid breaking imports; route to the enhanced code.
"""

# Route all imports to the enhanced service
from .enhanced_excel_import_service import EnhancedExcelImportService

# Create an alias so existing code using ExcelImportService still works
ExcelImportService = EnhancedExcelImportService

# For any code that imported specific functions/classes, re-export them
from .enhanced_excel_import_service import *  # noqa: F401, F403
