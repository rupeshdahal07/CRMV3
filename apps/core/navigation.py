"""
Sidebar navigation model.

Builds the grouped nav for the current user, honouring module view-permissions
and marking the active item from the request path. Kept out of templates so the
menu is defined once and testable.
"""

from django.urls import reverse

from . import permissions as perm

# icon key -> list of SVG path "d" strings (rendered by the _sidebar partial).
ICONS = {
    "grid": ["M4 4h6v6H4z", "M14 4h6v6h-6z", "M4 14h6v6H4z", "M14 14h6v6h-6z"],
    "board": ["M4 5h4v14H4z", "M10 5h4v9h-4z", "M16 5h4v11h-4z"],
    "book": ["M5 5a2 2 0 0 1 2-2h11v16H7a2 2 0 0 0-2 2z", "M5 19a2 2 0 0 1 2-2h11"],
    "cal": ["M5 6h14v14H5z", "M5 10h14", "M8 4v3", "M16 4v3"],
    "bell": ["M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6", "M10 20a2 2 0 0 0 4 0"],
    "slot": ["M12 7v5l3 2", "M4 12a8 8 0 1 0 16 0 8 8 0 0 0-16 0"],
    "inbox": ["M4 13l2-8h12l2 8v5H4z", "M4 13h5a3 3 0 0 0 6 0h5"],
    "chart": ["M4 20V4", "M4 20h16", "M8 16v-4", "M12 16V8", "M16 16v-7"],
    "flag": ["M6 21V4", "M6 4h11l-2 4 2 4H6"],
    "users": ["M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6", "M4 20a5 5 0 0 1 10 0", "M16 6a3 3 0 0 1 0 6", "M17 20a5 5 0 0 0-3-4.5"],
    "sliders": ["M4 8h10", "M18 8h2", "M4 16h4", "M12 16h8", "M14 6v4", "M8 14v4"],
    "user": ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8", "M5 20a7 7 0 0 1 14 0"],
}


def _module_item(user, key, label, icon, path, badge=None):
    """A module link, or None if the user can't view it."""
    if not perm.can_view(user, key):
        return None
    return {"label": label, "href": reverse("record_list", args=[key]), "icon": ICONS[icon], "badge": badge}


def build_nav(user, request_path, pending_followups=0):
    role = perm.role_of(user)
    is_staff_admin = role == "admin"
    is_admin_or_support_or_teacher = role in ("admin", "support", "teacher")

    overview = [
        {"label": "Dashboard", "href": reverse("dashboard"), "icon": ICONS["grid"], "badge": None},
        _module_item(user, "leads", "Leads & Calls", "board", request_path),
    ]
    admissions = [
        _module_item(user, "post-consultation-calls", "Post-Consult Calls", "bell", request_path),
        _module_item(user, "consultation-slots", "Consultation Slots", "slot", request_path),
        _module_item(user, "consultations", "Consultations", "user", request_path),
        _module_item(user, "followups", "Follow-ups", "inbox", request_path, badge=pending_followups or None),
    ]
    class_management = [
        _module_item(user, "cohorts", "Cohorts", "book", request_path),
        _module_item(user, "curriculum", "Curriculum", "cal", request_path),
        _module_item(user, "curriculum-chapters", "Curriculum Chapters", "cal", request_path),
        _module_item(user, "class-events", "Class Schedule", "cal", request_path),
        _module_item(user, "enrollments", "Enrollments", "chart", request_path),
    ]
    manage = [
        _module_item(user, "intake-targets", "Intake Targets", "flag", request_path),
    ]
    if is_staff_admin:
        manage.append({"label": "Users & Roles", "href": reverse("user_list"), "icon": ICONS["users"], "badge": None})
        manage.append({"label": "Manage Fields", "href": reverse("manage_fields_default"), "icon": ICONS["sliders"], "badge": None})
    if is_admin_or_support_or_teacher:
        manage.append({"label": "My Profile", "href": reverse("my_profile"), "icon": ICONS["user"], "badge": None})

    groups = [
        {"label": "Overview", "items": [i for i in overview if i]},
        {"label": "Admissions", "items": [i for i in admissions if i]},
        {"label": "Class management", "items": [i for i in class_management if i]},
        {"label": "Manage", "items": [i for i in manage if i]},
    ]
    groups = [g for g in groups if g["items"]]

    # Mark the active item: exact match for the dashboard, prefix match otherwise.
    for g in groups:
        for item in g["items"]:
            href = item["href"]
            if href == "/":
                item["active"] = request_path == "/"
            else:
                item["active"] = request_path.startswith(href)
    return groups
