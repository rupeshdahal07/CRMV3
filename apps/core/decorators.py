from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """Only Admins (role=admin or superuser) may proceed."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.role == "admin"):
            return HttpResponseForbidden("Only Admins can access this.")
        return view_func(request, *args, **kwargs)

    return wrapper


def roles_required(*roles):
    """Allow only the given roles (admins always allowed)."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            role = "admin" if request.user.is_superuser else request.user.role
            if role != "admin" and role not in roles:
                return HttpResponseForbidden("This page isn't available for your role.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
