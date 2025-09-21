window.addEventListener('DOMContentLoaded', function() {
  // find all table cells (in list_display) and detail fields whose text ends in “ UTC”
  document.querySelectorAll('td, .readonly').forEach(el => {
    const txt = el.textContent?.trim();
    if (!txt) return;
    // match ISO‐style “YYYY-MM-DD HH:MM:SS UTC”
    const m = txt.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC$/);
    if (!m) return;
    const dt = new Date(m[1] + 'Z');  // parse as UTC
    // format as Locale string with time zone, e.g. “7/9/2025, 11:16:54 PM PDT”
    el.textContent = dt.toLocaleString(undefined, {
      year:   'numeric',
      month:  'numeric',
      day:    'numeric',
      hour:   'numeric',
      minute: 'numeric',
      second: 'numeric',
      timeZoneName: 'short'
    });
  });
});