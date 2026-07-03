from apps.cohorts.models import Followup

from . import permissions as perm
from .navigation import build_nav


def nav_badges(request):
    """Pending follow-up count + the computed sidebar navigation for staff."""
    user = request.user
    if not user.is_authenticated:
        return {}
    role = perm.role_of(user)
    if role == "student":
        # Students use the separate portal shell, which has its own nav.
        return {}

    pending = 0
    if perm.can_view(user, "followups"):
        pending = perm.scope_queryset(user, "followups", Followup.objects.filter(done=False)).count()

    return {
        "pending_followups_count": pending,
        "nav_groups": build_nav(user, request.path, pending),
    }
