"""
Lightweight calendar template content tests (no Django/DB required).

These tests validate the presence of core elements and scripts used by the
standalone calendar template. They are intentionally minimal and resilient
to styling/library changes.
"""

from pathlib import Path


def _read_calendar_template() -> str:
    """Read the standalone calendar template reliably from repo root."""
    # tests/ui/<this_file> → parents[2] == project root
    project_root = Path(__file__).resolve().parents[2]
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
