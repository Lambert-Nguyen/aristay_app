"""
Excel file handling utilities for robust file processing.

This module provides utilities to handle Excel file uploads safely,
avoiding stream consumption issues and providing validation.
"""
import io
import hashlib
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def buffer_upload(uploaded_file) -> bytes:
    """
    Read the entire UploadedFile into memory as bytes.
    
    This prevents stream consumption issues by reading once
    and returning the raw bytes that can be used multiple times.
    
    Args:
        uploaded_file: Django UploadedFile instance
        
    Returns:
        bytes: The complete file content as bytes
    """
    uploaded_file.seek(0)  # Ensure we're at the start
    data = uploaded_file.read()
    uploaded_file.seek(0)  # Reset for any other consumers
    return data


def sha256_bytes(data: bytes) -> str:
    """
    Generate SHA-256 hash of bytes for deduplication/traceability.
    
    Args:
        data: Raw bytes to hash
        
    Returns:
        str: Hexadecimal SHA-256 hash
    """
    return hashlib.sha256(data).hexdigest()


def is_probably_xlsx(data: bytes) -> bool:
    """
    Quick check if bytes represent an XLSX file.
    
    XLSX files are ZIP archives, so they start with the ZIP signature "PK".
    This provides early validation before attempting pandas processing.
    
    Args:
        data: Raw file bytes
        
    Returns:
        bool: True if likely an XLSX file
    """
    return data.startswith(b"PK")


def validate_excel_file(uploaded_file) -> Tuple[bool, str, bytes]:
    """
    Comprehensive validation of uploaded Excel file.
    
    Args:
        uploaded_file: Django UploadedFile instance
        
    Returns:
        Tuple[bool, str, bytes]: (is_valid, error_message, file_bytes)
    """
    import os
    
    try:
        # Check file extension
        filename = getattr(uploaded_file, 'name', '')
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.xls':
            return False, "Legacy .xls files are not supported. Please upload .xlsx format.", b''
        elif ext != '.xlsx':
            return False, f"Unsupported file type '{ext}'. Please upload .xlsx format.", b''
        
        # Buffer the file
        data = buffer_upload(uploaded_file)
        
        # Check if empty
        if len(data) == 0:
            return False, "The uploaded file is empty.", b''
        
        # Check if it's actually an XLSX (ZIP format)
        if not is_probably_xlsx(data):
            return False, "This file is not a valid .xlsx (ZIP) file. Did you download an HTML error page?", b''
        
        logger.info(f"Excel file validated: {filename} ({len(data)} bytes, SHA-256: {sha256_bytes(data)[:8]}...)")
        
        return True, "", data
        
    except Exception as e:
        logger.error(f"Excel file validation failed: {e}", exc_info=True)
        return False, f"File validation error: {str(e)}", b''
