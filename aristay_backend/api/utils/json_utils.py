"""
JSON utility functions for the Aristay API
"""
import json
import logging

logger = logging.getLogger(__name__)


def extract_conflicts_json(errors_log: str) -> list:
    """
    Extracts conflicts JSON from import log errors_log field.
    
    Handles cases where additional content is appended after the JSON array.
    
    Args:
        errors_log: The errors_log field content from BookingImportLog
        
    Returns:
        list: Parsed conflicts data, or empty list if parsing fails
    """
    conflicts_data = []
    
    if "CONFLICTS_DATA:" not in errors_log:
        return conflicts_data
    
    conflicts_section = errors_log.split("CONFLICTS_DATA:")[1]
    
    try:
        # Find the JSON array boundaries
        json_start = conflicts_section.find('[')
        if json_start == -1:
            raise ValueError("No JSON array found")
        
        # Find the matching closing bracket
        bracket_count = 0
        json_end = -1
        in_string = False
        escape_next = False
        
        for i in range(json_start, len(conflicts_section)):
            char = conflicts_section[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break
        
        if json_end == -1:
            raise ValueError("No matching closing bracket found")
        
        # Extract just the JSON part
        conflicts_json = conflicts_section[json_start:json_end]
        conflicts_data = json.loads(conflicts_json)
        
    except (ValueError, json.JSONDecodeError) as parse_error:
        logger.error(f"Failed to parse conflicts JSON: {str(parse_error)}")
        # Try fallback parsing
        conflicts_lines = conflicts_section.split('\n')
        conflicts_json = conflicts_lines[0] if conflicts_lines else conflicts_section
        try:
            conflicts_data = json.loads(conflicts_json.strip())
        except json.JSONDecodeError:
            logger.error(f"Fallback parsing also failed for conflicts JSON")
            conflicts_data = []
    
    return conflicts_data
