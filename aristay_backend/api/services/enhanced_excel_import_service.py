"""
Enhanced Excel Import Service with Conflict Resolution

This enhanced service provides intelligent conflict detection and resolution
for booking imports, with different handling for platform vs direct bookings.
"""

# import pandas as pd  # Moved to function level to avoid circular imports
import json
import random
from datetime import datetime, timedelta, time
from decimal import Decimal
import logging
from typing import Dict, List, Tuple, Optional, Any
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

from api.models import (
    Booking, Property, Task, BookingImportLog, BookingImportTemplate
)

# Import base ExcelImportService from backup for inheritance
from .excel_import_service_backup import ExcelImportService

logger = logging.getLogger(__name__)


def _normalize_source(source: str) -> str:
    """Normalize source names to canonical values for consistent storage and lookup"""
    if not source:
        return ''
    
    source_lower = source.lower().strip()
    normalized = {
        'airbnb': 'Airbnb',
        'vrbo': 'VRBO', 
        'booking.com': 'Booking.com',
        'expedia': 'Expedia',
        'owner staying': 'Owner Staying',
        'owner': 'Owner',
        'direct': 'Direct',
        'directly': 'Direct'
    }
    return normalized.get(source_lower, source.title())


    def _map_external_status(self, external_status: str) -> str:
        """Centralized mapping of external status to internal status"""
        return _map_external_status(external_status)


def _map_external_status(external_status: str) -> str:
    """Global function for mapping external status to internal status"""
    if not external_status:
        return 'confirmed'  # Default
        
    external_lower = external_status.lower().strip()
    
    # Status mapping logic
    if external_lower in ['cancelled', 'canceled']:
        return 'cancelled'
    elif external_lower in ['pending', 'requested']:
        return 'booked'
    elif external_lower in ['completed', 'checked_out']:
        return 'completed'
    elif external_lower in ['owner_staying', 'owner staying']:
        return 'owner_staying'
    elif external_lower in ['currently_hosting', 'currently hosting', 'checked_in']:
        return 'currently_hosting'
    else:
        return 'confirmed'  # Default for confirmed, accepted, etc.
def _analyze_guest_name_difference(existing_name: str, new_name: str) -> Dict[str, Any]:
    """Analyze guest name differences to provide helpful conflict information"""
    if not existing_name or not new_name:
        return {
            'type': 'missing_data',
            'description': 'One name is missing',
            'likely_encoding_issue': False
        }
    
    import unicodedata
    import re
    
    # Try ftfy for mojibake detection if available
    try:
        import ftfy
        existing_fixed = ftfy.fix_text(existing_name)
        new_fixed = ftfy.fix_text(new_name)
        if existing_fixed != existing_name or new_fixed != new_name:
            existing_name = existing_fixed
            new_name = new_fixed
    except ImportError:
        pass  # Fall back gracefully if ftfy not available
    
    # Normalize for comparison (remove diacritics, case, extra spaces)
    def normalize(name):
        # Handle common character mappings
        char_mapping = {
            'ß': 'ss',  # German eszett
            'Ø': 'O',   # Danish/Norwegian O
            'ø': 'o',
            'Ł': 'L',   # Polish L
            'ł': 'l',
            'Æ': 'AE',  # Various AE ligatures
            'æ': 'ae',
            'Œ': 'OE',  # French OE ligature
            'œ': 'oe'
        }
        
        # Apply character mappings first
        for old_char, new_char in char_mapping.items():
            name = name.replace(old_char, new_char)
        
        # Remove diacritics
        normalized = unicodedata.normalize('NFKD', name)
        normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
        # Lowercase and clean spaces
        normalized = re.sub(r'\s+', ' ', normalized.lower().strip())
        return normalized
    
    existing_norm = normalize(existing_name)
    new_norm = normalize(new_name)
    
    # Check for various types of differences
    if existing_norm == new_norm:
        return {
            'type': 'diacritics_only',
            'description': f'Only diacritics/accent differences: "{existing_name}" vs "{new_name}"',
            'likely_encoding_issue': True
        }
    
    # Check if it might be an encoding issue (like MĂ¼ller → Muller)
    # Look for non-ASCII characters in existing that become ASCII in new
    existing_has_non_ascii = any(ord(c) > 127 for c in existing_name)
    new_is_mostly_ascii = all(ord(c) < 127 for c in new_name)
    
    if existing_has_non_ascii and new_is_mostly_ascii and len(existing_name) > len(new_name):
        return {
            'type': 'encoding_correction',
            'description': f'Possible encoding fix: "{existing_name}" → "{new_name}"',
            'likely_encoding_issue': True
        }
    
    # Check for simple typo corrections vs significant changes
    if abs(len(existing_name) - len(new_name)) <= 2 and len(set(existing_norm) & set(new_norm)) / max(len(existing_norm), len(new_norm)) > 0.5:
        return {
            'type': 'minor_correction',
            'description': f'Minor name correction: "{existing_name}" → "{new_name}"',
            'likely_encoding_issue': False
        }
    
    return {
        'type': 'significant_change',
        'description': f'Significant name change: "{existing_name}" → "{new_name}"',
        'likely_encoding_issue': False
    }


class ConflictType:
    """Types of conflicts that can occur during import"""
    DATE_CHANGE = 'date_change'
    GUEST_CHANGE = 'guest_change'
    PROPERTY_CHANGE = 'property_change'
    STATUS_CHANGE = 'status_change'
    DUPLICATE_DIRECT = 'duplicate_direct'


class BookingConflict:
    """Represents a conflict between existing booking and Excel data"""
    
    def __init__(self, existing_booking: Booking, excel_data: Dict[str, Any], conflict_types: List[str], row_number: int):
        self.existing_booking = existing_booking
        self.excel_data = excel_data
        self.conflict_types = conflict_types
        self.row_number = row_number
        self.confidence_score = self._calculate_confidence()
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence that these are the same booking (0.0 - 1.0)"""
        score = 0.0
        
        # External code match (highest weight)
        if self.existing_booking.external_code == self.excel_data.get('external_code'):
            score += 0.4
        
        # Guest name match
        if self.existing_booking.guest_name.lower() == self.excel_data.get('guest_name', '').lower():
            score += 0.3
        
        # Property match
        if self.existing_booking.property.name == self.excel_data.get('property_name'):
            score += 0.2
        
        # Date overlap - handle both date and datetime objects safely
        excel_start = self.excel_data.get('start_date')
        excel_end = self.excel_data.get('end_date')
        if excel_start and excel_end:
            # Safe date extraction for existing booking dates
            existing_start = self.existing_booking.check_in_date
            if hasattr(existing_start, 'date'):
                existing_start = existing_start.date()
            
            existing_end = self.existing_booking.check_out_date
            if hasattr(existing_end, 'date'):
                existing_end = existing_end.date()
            
            # Safe date extraction for Excel dates
            if hasattr(excel_start, 'date'):
                excel_start_date = excel_start.date()
            else:
                excel_start_date = excel_start
                
            if hasattr(excel_end, 'date'):
                excel_end_date = excel_end.date()
            else:
                excel_end_date = excel_end
            
            if excel_start_date == existing_start and excel_end_date == existing_end:
                score += 0.1
            elif (excel_start_date <= existing_end and excel_end_date >= existing_start):
                score += 0.05  # Partial overlap
        
        return score
    
    def get_changes_summary(self) -> Dict[str, Any]:
        """Get detailed summary of what would change"""
        changes = {}
        
        # Date changes
        if ConflictType.DATE_CHANGE in self.conflict_types:
            excel_start = self.excel_data.get('start_date')
            excel_end = self.excel_data.get('end_date')
            changes['dates'] = {
                'current': {
                    'check_in': self.existing_booking.check_in_date.strftime('%Y-%m-%d'),
                    'check_out': self.existing_booking.check_out_date.strftime('%Y-%m-%d')
                },
                'excel': {
                    'check_in': excel_start.strftime('%Y-%m-%d') if excel_start else None,
                    'check_out': excel_end.strftime('%Y-%m-%d') if excel_end else None
                }
            }
        
        # Guest changes with analysis
        if ConflictType.GUEST_CHANGE in self.conflict_types:
            guest_analysis = self.excel_data.get('_guest_name_analysis', {})
            changes['guest'] = {
                'current': self.existing_booking.guest_name,
                'excel': self.excel_data.get('guest_name'),
                'analysis': guest_analysis.get('description', 'Guest name change'),
                'likely_encoding_issue': guest_analysis.get('likely_encoding_issue', False),
                'change_type': guest_analysis.get('type', 'unknown')
            }
        
        # Status changes
        if ConflictType.STATUS_CHANGE in self.conflict_types:
            changes['status'] = {
                'current': self.existing_booking.external_status,
                'excel': self.excel_data.get('external_status')
            }
        
        return changes


class EnhancedExcelImportService(ExcelImportService):
    """Enhanced service with intelligent conflict detection and resolution"""
    
    def __init__(self, user: User, template: Optional[BookingImportTemplate] = None):
        super().__init__(user, template)
        self.conflicts_detected = []
        self.auto_updated_count = 0
        self.requires_review = False
    
    def import_excel_file(self, excel_file, sheet_name: str = 'Cleaning schedule') -> Dict[str, Any]:
        """Enhanced import with conflict detection"""
        try:
            import pandas as pd
            # Create import log
            self.import_log = self._create_import_log(excel_file)
            
            # Read Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            self.total_rows = len(df)
            
            logger.info(f"Starting enhanced Excel import: {self.total_rows} rows")
            
            # Process each row with conflict detection
            processed_rows = 0
            for index, row in df.iterrows():
                try:
                    if row.isna().all():
                        continue
                    
                    # Use enumerate to get proper index
                    row_num = processed_rows + 2
                    result = self._process_booking_row_with_conflicts(row, row_num)
                    processed_rows += 1
                    
                except Exception as e:
                    row_num = processed_rows + 2
                    error_msg = f"Row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.error(error_msg)
                    processed_rows += 1
            
            # Update import log with conflicts
            self._update_import_log()
            
            # 4. Create automated tasks for imported bookings
            task_count = 0
            if hasattr(self, 'import_log') and self.import_log:
                created_bookings = getattr(self.import_log, 'created_bookings', [])
                if created_bookings:
                    task_count = self.create_automated_tasks(created_bookings)
                    self.import_log.total_tasks_created = task_count
                    self.import_log.save()
            
            # Store conflicts in import log for later review
            if self.conflicts_detected:
                conflicts_data = [self._serialize_conflict(c) for c in self.conflicts_detected]
                self.import_log.errors_log += f"\n\nCONFLICTS_DATA:{json.dumps(conflicts_data)}"
                self.import_log.save()
            
            # Prepare result
            result = {
                'success': True,
                'total_rows': self.total_rows,
                'processed_rows': processed_rows,
                'successful_imports': self.success_count,
                'auto_updated': self.auto_updated_count,
                'conflicts_detected': len(self.conflicts_detected),
                'requires_review': self.requires_review,
                'errors_count': len(self.errors),
                'warnings_count': len(self.warnings),
                'errors': self.errors,
                'warnings': self.warnings
            }
            
            # Add conflicts for review if any
            if self.conflicts_detected:
                result['conflicts'] = [self._serialize_conflict(c) for c in self.conflicts_detected]
                result['import_session_id'] = self.import_log.pk
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced Excel import failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'total_rows': self.total_rows,
                'errors': self.errors
            }
    
    def _extract_booking_data_enhanced(self, row, row_number: int) -> Optional[Dict]:
        """Extract booking data WITHOUT automatic external code suffix addition"""
        try:
            import pandas as pd
            import random
            from api.models import Booking
            
            # Map Excel columns to our fields
            data = {}
            
            # Map columns with fallbacks for variations
            column_mappings = {
                'external_code': ['Confirmation code'],
                'external_status': ['Status'],
                'guest_name': ['Guest name'],
                'guest_contact': ['Contact'],
                'source': ['Booking source', 'Airbnb/VRBO'],  # Handle both column names
                'listing_name': ['Listing'],
                'earnings_amount': ['Earnings'],
                'booked_on': ['Booked'],
                'adults': ['# of adults'],
                'children': ['# of children'],
                'infants': ['# of infants'],
                'start_date': ['Start date'],
                'end_date': ['End date'],
                'nights': ['# of nights'],
                'property_label_raw': ['Properties'],
                'same_day_note': ['Check ', 'Check 1']
            }
            
            # Process each mapping
            for field_name, possible_columns in column_mappings.items():
                value = None
                for col_name in possible_columns:
                    if col_name in row.index and pd.notna(row[col_name]):
                        value = row[col_name]
                        break
                
                if value is not None:
                    data[field_name] = value
            
            # Clean and validate external code but DON'T add suffix
            if data.get('external_code'):
                external_code = str(data['external_code']).strip()
                
                # Check if external_code is actually a booking source (not a real confirmation code)
                generic_sources = ['directly', 'direct', 'owner staying', 'owner', 'walk-in', 'phone', 'email']
                if external_code.lower() in generic_sources:
                    # This is a generic source, not a real confirmation code
                    # Generate a unique code for direct bookings
                    counter = 1
                    while counter <= 99:
                        base_code = 'DIR'  # Direct booking prefix
                        generated_code = f"{base_code}{random.randint(100000, 999999)}"
                        
                        if not Booking.objects.filter(external_code=generated_code).exists():
                            data['external_code'] = generated_code
                            logger.info(f"Generated confirmation code for direct booking: {generated_code}")
                            break
                        counter += 1
                        if counter > 99:  # Safety limit
                            data['external_code'] = f"{base_code}{counter:03d}"
                            break
                else:
                    data['external_code'] = external_code
            
            # Generate confirmation code for platform bookings if missing
            if not data.get('external_code'):
                source = data.get('source', '').lower()
                if any(platform in source for platform in ['airbnb', 'vrbo', 'homeaway']):
                    # Generate platform-style code  
                    counter = 1
                    while counter <= 99:
                        if 'airbnb' in source:
                            base_code = 'HM'
                        elif 'vrbo' in source or 'homeaway' in source:
                            base_code = 'HA'
                        else:
                            base_code = 'BK'
                        
                        generated_code = f"{base_code}{random.randint(100000, 999999)}"
                        
                        if not Booking.objects.filter(external_code=generated_code).exists():
                            data['external_code'] = generated_code
                            logger.info(f"Generated confirmation code: {generated_code}")
                            break
                        counter += 1
                        if counter > 99:  # Safety limit
                            data['external_code'] = f"{base_code} {counter:02d}"
                            break
                else:
                    raise ValueError("Confirmation code is required for platform bookings")
            
            # Process dates properly with timezone awareness
            for date_field in ['start_date', 'end_date', 'booked_on']:
                if data.get(date_field):
                    value = data[date_field]
                    if isinstance(value, str):
                        # Try to parse string dates
                        try:
                            parsed_dt = pd.to_datetime(value).to_pydatetime()
                            # Make timezone-aware if naive
                            if parsed_dt.tzinfo is None:
                                from django.utils import timezone
                                parsed_dt = timezone.make_aware(parsed_dt)
                            data[date_field] = parsed_dt
                        except Exception:
                            logger.warning(f"Could not parse date field {date_field}: {value}")
                            if date_field in ['start_date', 'end_date']:
                                raise ValueError(f"Could not parse {date_field}: {value}")
                    elif isinstance(value, datetime):
                        # Make timezone-aware if naive
                        if value.tzinfo is None:
                            from django.utils import timezone
                            value = timezone.make_aware(value)
                        data[date_field] = value
                    elif hasattr(value, 'to_pydatetime'):
                        converted_dt = value.to_pydatetime()
                        # Make timezone-aware if naive
                        if converted_dt.tzinfo is None:
                            from django.utils import timezone
                            converted_dt = timezone.make_aware(converted_dt)
                        data[date_field] = converted_dt
            
            # Process numeric fields
            for numeric_field in ['adults', 'children', 'infants', 'nights']:
                if data.get(numeric_field):
                    try:
                        data[numeric_field] = int(float(data[numeric_field]))
                    except (ValueError, TypeError):
                        data[numeric_field] = 0 if numeric_field != 'adults' else 1
            
            # Process earnings
            if data.get('earnings_amount'):
                try:
                    # Remove currency symbols and convert to Decimal
                    earnings_str = str(data['earnings_amount']).replace('$', '').replace(',', '')
                    data['earnings_amount'] = Decimal(earnings_str)
                except (ValueError, TypeError):
                    data['earnings_amount'] = None
            
            # Skip the duplicate external code logic that adds "#" suffixes
            # The enhanced service will handle conflicts in _detect_conflicts()
            
            # Validate required fields
            if not data.get('start_date') or not data.get('end_date'):
                raise ValueError("Start date and end date are required")
            if not data.get('guest_name'):
                raise ValueError("Guest name is required")
            
            # Calculate nights if not provided or invalid
            if not data.get('nights') and data.get('start_date') and data.get('end_date'):
                try:
                    if isinstance(data['start_date'], datetime) and isinstance(data['end_date'], datetime):
                        nights = (data['end_date'] - data['start_date']).days
                        data['nights'] = max(1, nights)  # Ensure at least 1 night
                except Exception:
                    data['nights'] = 1  # Fallback
            
            return data
            
        except Exception as e:
            logger.error(f"Row {row_number}: Error extracting booking data: {str(e)}")
            self.errors.append(f"Row {row_number}: {str(e)}")
            return None
    
    def _process_booking_row_with_conflicts(self, row, row_number: int):
        """Process single row with enhanced conflict detection"""
        
        # Extract booking data WITHOUT automatic external code suffix logic
        booking_data = self._extract_booking_data_enhanced(row, row_number)
        if not booking_data:
            return
        
        # Find or create property
        property_obj = self._find_or_create_property(booking_data['property_label_raw'])
        if not property_obj:
            raise ValueError(f"Could not create property: {booking_data['property_label_raw']}")
        
        booking_data['property_name'] = property_obj.name
        
        # Enhanced conflict detection
        conflict_result = self._detect_conflicts(booking_data, property_obj, row_number)
        
        if conflict_result['has_conflicts']:
            if conflict_result['auto_resolve']:
                # Platform booking - auto update
                self._auto_update_booking(conflict_result['existing_booking'], booking_data, row)
                self.auto_updated_count += 1
                self.success_count += 1
                logger.info(f"Auto-updated platform booking: {conflict_result['existing_booking'].external_code}")
            else:
                # Direct/Owner booking OR exact duplicate - handle appropriately
                if conflict_result.get('is_exact_duplicate', False):
                    # Skip exact duplicates
                    logger.info(f"Skipped exact duplicate: Row {row_number}")
                    return  # Skip creating duplicate booking
                else:
                    # Add to conflicts for manual review
                    self.conflicts_detected.append(conflict_result['conflict'])
                    self.requires_review = True
                    logger.info(f"Conflict detected for review: Row {row_number}")
                    return  # Don't create booking, wait for manual resolution
        else:
            # No conflicts - create new booking
            new_booking = self._create_booking(booking_data, property_obj, row)
            # REMOVED: self._create_cleaning_task(new_booking) - now handled by AutoTaskTemplates
            self.success_count += 1
            logger.info(f"Created new booking: {new_booking.external_code}")
    
    def _detect_conflicts(self, booking_data: Dict[str, Any], property_obj: Property, row_number: int) -> Dict[str, Any]:
        """Enhanced conflict detection with comprehensive duplicate detection"""
        
        external_code = booking_data.get('external_code')
        guest_name = booking_data.get('guest_name')
        source = _normalize_source(booking_data.get('source', ''))  # GPT Agent Fix: Normalize source
        start_date = booking_data.get('start_date')
        end_date = booking_data.get('end_date')
        
        # Check if this is a direct/owner booking using normalized source
        is_direct_booking = 'Direct' in source or 'Owner' in source
        
        existing_booking = None
        
        # Step 0: Check for same source+code on a different property → property_change conflict
        if external_code and source:
            cross_property_bookings = Booking.objects.filter(
                source__iexact=source,
                external_code=external_code
            ).exclude(property=property_obj)
            
            if cross_property_bookings.exists():
                existing_booking = cross_property_bookings.first()
                if existing_booking:  # Type guard
                    conflict = BookingConflict(
                        existing_booking=existing_booking,
                        excel_data=booking_data,
                        conflict_types=[ConflictType.PROPERTY_CHANGE],
                        row_number=row_number,
                    )
                    return {
                        'has_conflicts': True,
                        'auto_resolve': False,  # never auto-resolve property changes
                        'existing_booking': existing_booking,
                        'conflict': conflict,
                        'is_exact_duplicate': False
                    }
        
        # Step 1: Check for exact external code match (for platform bookings with original codes)
        # GPT Agent Fix: Use scoped booking lookup with case-insensitive source comparison
        if external_code:
            existing_bookings = Booking.objects.filter(
                property=property_obj,
                source__iexact=source,  # Case-insensitive source comparison
                external_code=external_code
            )
            
            if existing_bookings.exists():
                existing_booking = existing_bookings.first()
                if existing_booking:
                    conflict_types = self._identify_conflict_types(existing_booking, booking_data)
                    
                    # Check if this is an exact duplicate (no meaningful changes)
                    is_exact_duplicate = len(conflict_types) == 0
                    
                    # Status-only changes should be auto-updated for platform bookings
                    is_status_only_change = len(conflict_types) == 1 and ConflictType.STATUS_CHANGE in conflict_types
                    
                    # Guest name changes should always require manual review (per user requirement)
                    has_guest_change = ConflictType.GUEST_CHANGE in conflict_types
                    
                    # AGENT FIX: Only auto-resolve status-only changes for platform bookings
                    auto_resolve = (not is_direct_booking) and is_status_only_change
                    
                    # Always flag external code matches as conflicts for review
                    conflict = BookingConflict(existing_booking, booking_data, conflict_types, row_number)
                    return {
                        'has_conflicts': True,
                        'auto_resolve': auto_resolve,
                        'existing_booking': existing_booking,
                        'conflict': conflict,
                        'is_exact_duplicate': is_exact_duplicate and not is_status_only_change
                    }
        
        # Step 2: Comprehensive duplicate detection for ALL bookings (platform and direct)
        # This catches cases where platform bookings had generated codes on first import
        if guest_name and start_date and end_date and isinstance(start_date, datetime) and isinstance(end_date, datetime):
            # GPT Agent Fix: Use __date lookups to handle date-vs-datetime mismatches properly
            potential_duplicates = Booking.objects.filter(
                property=property_obj,
                guest_name__iexact=guest_name,
                check_in_date__date=start_date.date(),
                check_out_date__date=end_date.date()
            )
            
            if potential_duplicates.exists():
                existing_booking = potential_duplicates.first()
                if existing_booking:
                    conflict_types = self._identify_conflict_types(existing_booking, booking_data)
                    
                    # Check if this is an exact duplicate (no meaningful differences)
                    is_exact_duplicate = len(conflict_types) == 0
                    
                    # Status-only changes should be auto-updated for platform bookings
                    is_status_only_change = len(conflict_types) == 1 and ConflictType.STATUS_CHANGE in conflict_types
                    
                    # Guest name changes should always require manual review (per user requirement)
                    has_guest_change = ConflictType.GUEST_CHANGE in conflict_types
                    
                    # AGENT FIX: Only auto-resolve status-only changes for platform bookings
                    auto_resolve = (not is_direct_booking) and is_status_only_change
                    
                    # This is likely a duplicate from the same Excel file
                    conflict = BookingConflict(existing_booking, booking_data, conflict_types, row_number)
                    return {
                        'has_conflicts': True,
                        'auto_resolve': auto_resolve,
                        'existing_booking': existing_booking,
                        'conflict': conflict,
                        'is_exact_duplicate': is_exact_duplicate and not is_status_only_change
                    }
            
            # Step 3: Check for date overlaps (different from exact match)
            overlapping_bookings = Booking.objects.filter(
                property=property_obj,
                guest_name__iexact=guest_name,
                check_in_date__lt=end_date.date(),
                check_out_date__gt=start_date.date()
            ).exclude(
                check_in_date__date=start_date.date(),
                check_out_date__date=end_date.date()
            )
            
            if overlapping_bookings.exists():
                existing_booking = overlapping_bookings.first()
                if existing_booking:
                    conflict_types = self._identify_conflict_types(existing_booking, booking_data)
                    conflict = BookingConflict(existing_booking, booking_data, conflict_types, row_number)
                    
                    return {
                        'has_conflicts': True,
                        'auto_resolve': False,  # Date overlaps always need manual review
                        'existing_booking': existing_booking,
                        'conflict': conflict,
                        'is_exact_duplicate': False  # Overlaps are not exact duplicates
                    }
        
        return {
            'has_conflicts': False,
            'auto_resolve': False,
            'existing_booking': None,
            'conflict': None,
            'is_exact_duplicate': False
        }
    
    def _identify_conflict_types(self, existing_booking: Booking, booking_data: Dict[str, Any]) -> List[str]:
        """Identify specific types of conflicts"""
        conflicts = []
        
        # Date changes - handle both date and datetime objects
        existing_start = existing_booking.check_in_date
        existing_end = existing_booking.check_out_date
        
        # Convert to date if datetime
        if hasattr(existing_start, 'date'):
            existing_start = existing_start.date()
        if hasattr(existing_end, 'date'):
            existing_end = existing_end.date()
            
        excel_start = booking_data.get('start_date')
        excel_end = booking_data.get('end_date')
        
        if excel_start and excel_end and isinstance(excel_start, datetime) and isinstance(excel_end, datetime):
            if existing_start != excel_start.date() or existing_end != excel_end.date():
                conflicts.append(ConflictType.DATE_CHANGE)
        
        # Guest name changes with detailed analysis
        existing_guest = existing_booking.guest_name or ''
        new_guest = booking_data.get('guest_name', '') or ''
        
        if existing_guest.lower() != new_guest.lower():
            conflicts.append(ConflictType.GUEST_CHANGE)
            # Store analysis for conflict resolution UI
            name_analysis = _analyze_guest_name_difference(existing_guest, new_guest)
            booking_data['_guest_name_analysis'] = name_analysis
        
        # Status changes
        if existing_booking.external_status != booking_data.get('external_status'):
            conflicts.append(ConflictType.STATUS_CHANGE)
        
        # Property changes
        existing_property = existing_booking.property.name
        excel_property = booking_data.get('property_name', '')
        
        if existing_property != excel_property:
            conflicts.append(ConflictType.PROPERTY_CHANGE)
        
        return conflicts
    
    def _auto_update_booking(self, booking: Booking, booking_data: Dict[str, Any], row):
        """Automatically update platform bookings - AGENT FIX: Only update status for auto-resolve"""
        try:
            # AGENT FIX: Only update external_status and internal status for auto-resolved conflicts
            if 'external_status' in booking_data:
                booking.external_status = booking_data['external_status']
                # Use unified status mapping for consistency
                booking.status = _map_external_status(booking_data['external_status'])
            
            # Update import tracking
            booking.last_import_update = timezone.now()
            booking.save()
            
        except Exception as e:
            logger.error(f"Failed to auto-update booking {booking.external_code}: {e}")
            raise
    
    def _serialize_conflict(self, conflict: BookingConflict) -> Dict[str, Any]:
        """Serialize conflict for frontend consumption with hardened JSON handling"""
        # GPT Agent Fix: Harden JSON serialization with deep serialization
        from datetime import date
        
        def _safe(value):
            """Safely serialize scalar values that might not be JSON serializable"""
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(value, date):
                return value.strftime('%Y-%m-%d')
            if hasattr(value, 'pk'):  # Model instances
                return value.pk
            try:
                return str(value)
            except:
                return '<serialization error>'
        
        def _safe_deep(obj):
            """Deep serialization for nested dicts/lists"""
            if isinstance(obj, dict):
                return {k: _safe_deep(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_safe_deep(v) for v in obj]
            return _safe(obj)
        
        return {
            'row_number': _safe(conflict.row_number),
            'confidence_score': _safe(conflict.confidence_score),
            'conflict_types': _safe_deep(conflict.conflict_types),  # Use deep serialization for lists
            'existing_booking': {
                'id': _safe(conflict.existing_booking.pk),
                'external_code': _safe(conflict.existing_booking.external_code),
                'guest_name': _safe(conflict.existing_booking.guest_name),
                'property_name': _safe(conflict.existing_booking.property.name),
                'check_in_date': _safe(conflict.existing_booking.check_in_date),
                'check_out_date': _safe(conflict.existing_booking.check_out_date),
                'status': _safe(conflict.existing_booking.status),
                'external_status': _safe(conflict.existing_booking.external_status),
                'source': _safe(conflict.existing_booking.source)
            },
            'excel_data': {
                'external_code': _safe(conflict.excel_data.get('external_code')),
                'guest_name': _safe(conflict.excel_data.get('guest_name')),
                'property_name': _safe(conflict.excel_data.get('property_name')),
                'start_date': _safe(conflict.excel_data.get('start_date')),
                'end_date': _safe(conflict.excel_data.get('end_date')),
                'external_status': _safe(conflict.excel_data.get('external_status')),
                'source': _safe(conflict.excel_data.get('source'))
            },
            'changes_summary': _safe_deep(conflict.get_changes_summary())
        }
    
    def create_automated_tasks(self, bookings):
        """Create tasks from active templates for imported bookings"""
        from ..models import AutoTaskTemplate
        
        task_count = 0
        try:
            active_templates = AutoTaskTemplate.objects.filter(is_active=True)
            
            for booking in bookings:
                for template in active_templates:
                    task = template.create_task_for_booking(booking)
                    if task:
                        task_count += 1
                        logger.info(f"Created task '{task.title}' for booking {booking.external_code}")
                        
        except Exception as e:
            logger.error(f"Error creating automated tasks: {str(e)}")
            
        return task_count
    
    def _create_cleaning_task(self, *args, **kwargs):
        """Override legacy auto-cleaning to avoid duplicate template tasks."""
        return None
    
    def _safe_format_date(self, date_value: Any) -> Optional[str]:
        """Safely format date value for JSON serialization"""
        if date_value is None:
            return None
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        if hasattr(date_value, 'date'):
            return date_value.date().strftime('%Y-%m-%d')
        return str(date_value) if date_value else None


class ConflictResolutionService:
    """Service to handle conflict resolution decisions"""
    
    def __init__(self, user: User):
        self.user = user
    
    def resolve_conflicts(self, import_session_id: int, resolutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts based on user decisions
        
        resolutions: List of {
            'conflict_index': int,
            'action': 'update_existing' | 'create_new' | 'skip',
            'apply_changes': List[str]  # which fields to update
        }
        """
        try:
            # Make import id available to update helpers
            self.current_import_id = import_session_id
            import_log = BookingImportLog.objects.get(id=import_session_id)
            results = {
                'updated': 0,
                'created': 0,
                'skipped': 0,
                'errors': []
            }
            
            # Extract conflicts from import log
            conflicts_data = []
            if "CONFLICTS_DATA:" in import_log.errors_log:
                conflicts_json = import_log.errors_log.split("CONFLICTS_DATA:")[1]
                conflicts_data = json.loads(conflicts_json)
            
            for resolution in resolutions:
                try:
                    conflict_data = conflicts_data[resolution['conflict_index']]
                    action = resolution['action']
                    
                    if action == 'update_existing':
                        self._update_existing_booking(conflict_data, resolution.get('apply_changes', []))
                        results['updated'] += 1
                    elif action == 'create_new':
                        self._create_new_booking(conflict_data)
                        results['created'] += 1
                    elif action == 'skip':
                        results['skipped'] += 1
                        
                except Exception as e:
                    results['errors'].append(f"Failed to resolve conflict {resolution['conflict_index']}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {str(e)}")
            raise
    
    def _update_existing_booking(self, conflict_data: Dict[str, Any], apply_changes: List[str]):
        """Update existing booking with selected changes"""
        booking = Booking.objects.get(id=conflict_data['existing_booking']['id'])
        excel_data = conflict_data['excel_data']
        changes_summary = conflict_data.get('changes_summary', {})
        
        # Track guest name changes for audit
        if 'guest_name' in apply_changes and 'guest_name' in excel_data:
            old_name = booking.guest_name
            new_name = excel_data['guest_name']
            booking.guest_name = new_name
            
            # Add audit entry for guest name changes
            guest_analysis = changes_summary.get('guest', {})
            change_type = guest_analysis.get('change_type', 'unknown')
            import_session_id = getattr(self, 'current_import_id', 'unknown')
            
            # Import AuditEvent model
            from api.models import AuditEvent
            
            # AGENT FIX: Use consistent AuditEvent schema with JSON changes
            AuditEvent.objects.create(
                object_type='Booking',
                object_id=str(booking.pk),
                action='update',
                actor=self.user,
                changes={
                    'guest_name': {
                        'old': old_name,
                        'new': new_name
                    },
                    'metadata': {
                        'change_type': change_type,
                        'import_id': import_session_id
                    }
                }
            )
        
        if 'dates' in apply_changes:
            if 'start_date' in excel_data:
                start_date = excel_data['start_date']
                if isinstance(start_date, str):
                    booking.check_in_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                elif isinstance(start_date, datetime):
                    booking.check_in_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
            if 'end_date' in excel_data:
                end_date = excel_data['end_date']
                if isinstance(end_date, str):
                    booking.check_out_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                elif isinstance(end_date, datetime):
                    booking.check_out_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        if 'status' in apply_changes and 'external_status' in excel_data:
            booking.external_status = excel_data['external_status']
        
        booking.save()
    
    def _create_new_booking(self, conflict_data: Dict[str, Any]):
        """Create new booking from Excel data"""
        excel_data = conflict_data['excel_data']
        property_obj = Property.objects.get(name=excel_data['property_name'])
        
        # Handle external code - only add suffix for direct/owner bookings
        original_code = excel_data.get('external_code', 'UNKNOWN')
        source = excel_data.get('source', '').lower()
        is_direct_booking = 'direct' in source or 'owner' in source
        
        if is_direct_booking:
            # For direct bookings, add unique suffix to avoid conflicts
            counter = 1
            unique_code = f"{original_code} #{counter}"
            
            while Booking.objects.filter(external_code=unique_code).exists():
                counter += 1
                unique_code = f"{original_code} #{counter}"
        else:
            # For platform bookings (Airbnb, VRBO), keep original external code
            # Platform codes should be unique by nature
            unique_code = original_code
        
        # Handle dates
        start_date = excel_data.get('start_date')
        end_date = excel_data.get('end_date')
        
        if isinstance(start_date, str):
            check_in_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        elif isinstance(start_date, datetime):
            check_in_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
        else:
            check_in_date = timezone.now()  # Default fallback
        
        if isinstance(end_date, str):
            check_out_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
        elif isinstance(end_date, datetime):
            check_out_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        else:
            check_out_date = timezone.now() + timedelta(days=1)  # Default fallback
        
        booking = Booking.objects.create(
            property=property_obj,
            external_code=unique_code,
            guest_name=excel_data.get('guest_name', 'Unknown Guest'),
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            external_status=excel_data.get('external_status', ''),
            source=excel_data.get('source', 'Import')
        )
        
        return booking

    def _create_booking(self, booking_data: Dict, property_obj: Property, row) -> Booking:
        """Create new booking from Excel data with scoped external code suffixing to prevent duplicates"""
        
        # GPT Agent Fix: Add scoped external code suffixing to prevent duplicate creation
        original_code = booking_data.get('external_code', '')
        source = _normalize_source(booking_data.get('source', ''))
        
        # Ensure unique external_code within property + source scope
        code = original_code
        i = 1
        while Booking.objects.filter(
            property=property_obj,
            source__iexact=source,
            external_code=code
        ).exists():
            i += 1
            code = f"{original_code} #{i}"
        
        # Update booking_data with the unique code and normalized source
        booking_data = booking_data.copy()  # Don't modify original
        booking_data['external_code'] = code
        booking_data['source'] = source  # Store normalized source
        
        # Ensure nights field has a valid value
        nights_value = booking_data.get('nights')
        if nights_value is None or not isinstance(nights_value, (int, float)):
            # Calculate nights from start/end dates
            try:
                if isinstance(booking_data['start_date'], datetime) and isinstance(booking_data['end_date'], datetime):
                    nights_value = (booking_data['end_date'] - booking_data['start_date']).days
                    nights_value = max(1, nights_value)  # Ensure at least 1 night
                else:
                    nights_value = 1  # Fallback
            except Exception:
                nights_value = 1  # Fallback
        
        # Create booking with all the new fields - NO duplicate checking
        try:
            # Use unified status mapping
            external_status = booking_data.get('external_status', '')
            django_status = _map_external_status(external_status)
            
            # Simple row serialization
            import pandas as pd
            raw_row = {str(k): str(v) for k, v in row.items() if pd.notna(v)}
            
            booking = Booking.objects.create(
                property=property_obj,
                check_in_date=booking_data['start_date'],
                check_out_date=booking_data['end_date'],
                guest_name=booking_data['guest_name'],
                guest_contact=booking_data.get('guest_contact', ''),
                status=django_status,
                external_code=booking_data['external_code'],  # Use as-is, no suffix
                external_status=booking_data.get('external_status', ''),
                source=booking_data.get('source', ''),
                listing_name=booking_data.get('listing_name', ''),
                earnings_amount=booking_data.get('earnings_amount'),
                earnings_currency='USD',
                booked_on=booking_data.get('booked_on'),
                adults=booking_data.get('adults', 1),
                children=booking_data.get('children', 0),
                infants=booking_data.get('infants', 0),
                nights=nights_value,
                check_in_time=booking_data.get('check_in_time'),
                check_out_time=booking_data.get('check_out_time'),
                property_label_raw=booking_data['property_label_raw'],
                same_day_note=booking_data.get('same_day_note', ''),
                same_day_flag=bool(booking_data.get('same_day_note'))
                # Skip raw_row for now to avoid type issues
            )
            
            return booking
            
        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            raise

    def _create_booking_from_data(self, booking_data: Dict, property_obj):
        """Wrapper method for backward compatibility"""
        return self._create_booking(booking_data, property_obj, row={})
