"""
Lightweight calendar template content tests (no Django/DB required).

These tests validate the presence of core elements and scripts used by the
standalone calendar template. They are intentionally minimal and resilient
to styling/library changes.
"""

from pathlib import Path


def _read_calendar_template() -> str:
    """Read the standalone calendar template reliably from repo root."""
    project_root = Path(__file__).resolve().parents[3]
    template_path = project_root / "aristay_backend" / "api" / "templates" / "calendar" / "calendar_view.html"
    assert template_path.exists(), f"Calendar template not found at {template_path}"
    return template_path.read_text(encoding="utf-8")


def test_calendar_template_basic_structure():
    content = _read_calendar_template()
    assert "<!DOCTYPE html>" in content
    assert "<html" in content and "</html>" in content
    assert "<head>" in content and "<body>" in content


def test_calendar_template_core_elements():
    content = _read_calendar_template()
    # Calendar container and filter controls
    assert "id=\"calendar\"" in content
    assert "id=\"propertyFilter\"" in content
    assert "id=\"statusFilter\"" in content
    assert "id=\"assignedToFilter\"" in content


def test_calendar_template_javascript_functions_present():
    content = _read_calendar_template()
    assert "loadCalendarEvents" in content
    assert "loadFilterOptions" in content
    assert "showEventDetails" in content
    assert "applyFilters" in content
    assert "clearFilters" in content
    # FullCalendar v6 API used in template
    assert "dateClick" in content
    assert "eventDidMount" in content


def test_calendar_template_fullcalendar_integration():
    content = _read_calendar_template()
    # CDN includes and core handlers
    assert "fullcalendar" in content
    assert "eventClick" in content
    assert "dateClick" in content
    assert "eventDidMount" in content


def test_calendar_template_api_endpoints():
    content = _read_calendar_template()
    # Endpoint paths used by the JS in the template
    assert "/api/calendar/events/" in content
    assert "/api/calendar/properties/" in content
    assert "/api/calendar/users/" in content
    assert "/api/calendar/day_events/" in content


def test_calendar_template_modal_and_styles_present():
    content = _read_calendar_template()
    assert "id=\"eventModal\"" in content
    # Event styling classes
    assert ".event-task" in content
    assert ".event-booking" in content


def test_calendar_template_cdn_assets_present():
    content = _read_calendar_template()
    # FullCalendar and FontAwesome CDNs
    assert "cdn.jsdelivr.net/npm/fullcalendar" in content
    assert "cdnjs.cloudflare.com/ajax/libs/font-awesome" in content


def test_calendar_template_error_logging_present():
    content = _read_calendar_template()
    # We log errors to console on fetch failures
    assert "console.error" in content


def test_calendar_template_error_handling():
    """Test calendar template has error handling."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for error handling
    assert 'error' in content
    assert 'catch' in content
    assert 'alert' in content
    assert 'danger' in content


def test_calendar_template_api_endpoints():
    """Test calendar template references API endpoints."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for API endpoint references
    assert '/api/calendar/events/' in content
    assert '/api/calendar/filter-options/' in content
    assert '/api/calendar/day-events/' in content
    assert '/api/calendar/tasks/' in content
    assert '/api/calendar/bookings/' in content


def test_calendar_template_responsive_design():
    """Test calendar template has responsive design elements."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for responsive design
    assert 'col-md-' in content
    assert 'col-lg-' in content
    assert 'col-sm-' in content
    assert 'd-block' in content
    assert 'd-md-block' in content


def test_calendar_template_accessibility():
    """Test calendar template has accessibility features."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for accessibility features
    assert 'aria-' in content
    assert 'role=' in content
    assert 'alt=' in content
    assert 'title=' in content


def test_calendar_template_meta_tags():
    """Test calendar template has proper meta tags."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for meta tags
    assert '<meta' in content
    assert 'charset=' in content
    assert 'viewport' in content
    assert 'name=' in content


def test_calendar_template_favicon():
    """Test calendar template has favicon."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for favicon
    assert 'favicon' in content
    assert 'icon' in content


def test_calendar_template_fontawesome_integration():
    """Test calendar template integrates with FontAwesome."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for FontAwesome integration
    assert 'fontawesome' in content
    assert 'fa-' in content
    assert 'fas' in content


def test_calendar_template_bootstrap_classes():
    """Test calendar template uses Bootstrap classes."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Bootstrap classes
    assert 'btn' in content
    assert 'form-control' in content
    assert 'form-select' in content
    assert 'badge' in content
    assert 'text-' in content


def test_calendar_template_data_attributes():
    """Test calendar template has data attributes."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for data attributes
    assert 'data-' in content
    assert 'data-toggle' in content
    assert 'data-target' in content
    assert 'data-bs-' in content


def test_calendar_template_internationalization():
    """Test calendar template supports internationalization."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for i18n support
    assert '{% trans' in content
    assert '{% load i18n' in content


def test_calendar_template_debugging_support():
    """Test calendar template has debugging support."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for debugging support
    assert 'console.log' in content
    assert 'debug' in content


def test_calendar_template_performance_optimization():
    """Test calendar template has performance optimizations."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for performance optimizations
    assert 'async' in content
    assert 'defer' in content
    assert 'lazy' in content


def test_calendar_template_security_features():
    """Test calendar template has security features."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for security features
    assert 'csrf' in content
    assert 'token' in content
    assert 'nonce' in content


def test_calendar_template_cross_browser_compatibility():
    """Test calendar template has cross-browser compatibility."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for cross-browser compatibility
    assert 'polyfill' in content
    assert 'babel' in content
    assert 'es5' in content


def test_calendar_template_mobile_optimization():
    """Test calendar template has mobile optimization."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for mobile optimization
    assert 'mobile' in content
    assert 'touch' in content
    assert 'swipe' in content


def test_calendar_template_analytics_integration():
    """Test calendar template has analytics integration."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for analytics integration
    assert 'analytics' in content
    assert 'tracking' in content
    assert 'gtag' in content


def test_calendar_template_event_rendering():
    """Test calendar template has event rendering logic."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for event rendering
    assert 'event' in content
    assert 'render' in content
    assert 'display' in content


def test_calendar_template_event_styling():
    """Test calendar template has event styling."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for event styling
    assert 'style' in content
    assert 'color' in content
    assert 'background' in content


def test_calendar_template_event_processing():
    """Test calendar template has event processing logic."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for event processing
    assert 'process' in content
    assert 'handle' in content
    assert 'manage' in content


def test_calendar_template_filter_processing():
    """Test calendar template has filter processing logic."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for filter processing
    assert 'filter' in content
    assert 'search' in content
    assert 'query' in content


def test_calendar_template_data_processing():
    """Test calendar template has data processing logic."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for data processing
    assert 'data' in content
    assert 'json' in content
    assert 'parse' in content


def test_calendar_template_api_integration():
    """Test calendar template has API integration."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for API integration
    assert 'api' in content
    assert 'fetch' in content
    assert 'ajax' in content


def test_calendar_template_loading_states():
    """Test calendar template has loading states."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for loading states
    assert 'loading' in content
    assert 'state' in content
    assert 'status' in content


def test_calendar_template_error_display():
    """Test calendar template has error display."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for error display
    assert 'error' in content
    assert 'message' in content
    assert 'warning' in content


def test_calendar_template_success_callback():
    """Test calendar template has success callback."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for success callback
    assert 'success' in content
    assert 'callback' in content
    assert 'complete' in content


def test_calendar_template_url_generation():
    """Test calendar template has URL generation."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for URL generation
    assert 'url' in content
    assert 'href' in content
    assert 'link' in content


def test_calendar_template_modal_functionality():
    """Test calendar template has modal functionality."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for modal functionality
    assert 'modal' in content
    assert 'show' in content
    assert 'hide' in content


def test_calendar_template_button_elements():
    """Test calendar template has button elements."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for button elements
    assert '<button' in content
    assert 'btn' in content
    assert 'click' in content


def test_calendar_template_form_elements():
    """Test calendar template has form elements."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for form elements
    assert '<form' in content
    assert '<input' in content
    assert '<select' in content


def test_calendar_template_calendar_configuration():
    """Test calendar template has calendar configuration."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for calendar configuration
    assert 'config' in content
    assert 'option' in content
    assert 'setting' in content


def test_calendar_template_event_handlers():
    """Test calendar template has event handlers."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for event handlers
    assert 'handler' in content
    assert 'listener' in content
    assert 'callback' in content


def test_calendar_template_content_structure():
    """Test calendar template has proper content structure."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for content structure
    assert 'header' in content
    assert 'main' in content
    assert 'footer' in content
    assert 'section' in content


def test_calendar_template_css_classes():
    """Test calendar template has proper CSS classes."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for CSS classes
    assert 'class=' in content
    assert 'id=' in content
    assert 'style=' in content


def test_calendar_template_data_attributes():
    """Test calendar template has data attributes."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for data attributes
    assert 'data-' in content
    assert 'data-bs-' in content
    assert 'data-toggle' in content


def test_calendar_template_data_processing():
    """Test calendar template has data processing."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for data processing
    assert 'process' in content
    assert 'handle' in content
    assert 'manage' in content


def test_calendar_template_debugging_support():
    """Test calendar template has debugging support."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for debugging support
    assert 'debug' in content
    assert 'console' in content
    assert 'log' in content


def test_calendar_template_error_handling():
    """Test calendar template has error handling."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for error handling
    assert 'error' in content
    assert 'catch' in content
    assert 'try' in content


def test_calendar_template_event_processing():
    """Test calendar template has event processing."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for event processing
    assert 'event' in content
    assert 'process' in content
    assert 'handle' in content


def test_calendar_template_mobile_optimization():
    """Test calendar template has mobile optimization."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for mobile optimization
    assert 'mobile' in content
    assert 'responsive' in content
    assert 'touch' in content


def test_calendar_template_modal_elements():
    """Test calendar template has modal elements."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for modal elements
    assert 'modal' in content
    assert 'dialog' in content
    assert 'popup' in content


def test_calendar_template_modal_functionality():
    """Test calendar template has modal functionality."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for modal functionality
    assert 'modal' in content
    assert 'show' in content
    assert 'hide' in content


def test_calendar_template_performance_optimization():
    """Test calendar template has performance optimization."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for performance optimization
    assert 'performance' in content
    assert 'optimize' in content
    assert 'cache' in content


def test_calendar_template_responsive_design():
    """Test calendar template has responsive design."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for responsive design
    assert 'responsive' in content
    assert 'mobile' in content
    assert 'desktop' in content


def test_calendar_template_security_features():
    """Test calendar template has security features."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for security features
    assert 'security' in content
    assert 'csrf' in content
    assert 'token' in content


def test_calendar_template_success_callback():
    """Test calendar template has success callback."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for success callback
    assert 'success' in content
    assert 'callback' in content
    assert 'complete' in content


def test_calendar_template_url_generation():
    """Test calendar template has URL generation."""
    template_path = 'aristay_backend/api/templates/calendar/calendar_view.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for URL generation
    assert 'url' in content
    assert 'href' in content
    assert 'link' in content