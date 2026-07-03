from django import template

register = template.Library()

_OK_WORDS = {
    "active",
    "published",
    "done",
    "present",
    "ready",
    "completed",
    "started",
    "high",
    "yes",
    "active in class",
    "completed program",
    "attended live class",
    "open",
    "enrolled",
    "answered",
}
_WARN_WORDS = {
    "draft",
    "inactive",
    "absent",
    "not ready",
    "on hold",
    "cancelled",
    "no answer",
    "not interested",
    "low",
    "did not attend",
    "rescheduled",
    "follow-up needed",
    "no show",
    "not suitable",
    "full",
}


@register.filter
def status_badge(value):
    """Maps a status string to a chip variant: ok / warn / neutral."""
    text = str(value or "").strip().lower()
    if text in _OK_WORDS:
        return "ok"
    if text in _WARN_WORDS:
        return "warn"
    return "neutral"


@register.filter
def get_item(dictionary, key):
    """Dict lookup by variable key in templates."""
    if hasattr(dictionary, "get"):
        return dictionary.get(key)
    return None


@register.filter
def is_bool(value):
    """True only for actual booleans (so list cells can render Yes/No chips)."""
    return isinstance(value, bool)


@register.filter
def is_url(value):
    """True for http(s) URLs, so list cells can render them as clickable links."""
    return isinstance(value, str) and value.startswith(("http://", "https://"))


@register.filter
def field_type(field):
    """Best-effort widget category for styling form fields: check / select / textarea / input."""
    widget = getattr(getattr(field, "field", None), "widget", None)
    name = type(widget).__name__ if widget else ""
    if name in ("CheckboxInput",):
        return "check"
    if name in ("Select", "SelectMultiple", "NullBooleanSelect"):
        return "select"
    if name in ("CheckboxSelectMultiple",):
        return "checks"
    if name in ("Textarea",):
        return "textarea"
    return "input"
