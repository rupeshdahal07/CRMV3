"""
Student account provisioning.

Every Lead gets a real student-role login (auto-created when the Lead is made)
that routes to the Student Portal. `plain_password` is kept in sync so staff can
view/share the credentials.
"""

import random
import string

from django.utils.text import slugify

from .models import User


def _generate_username(full_name):
    first = (full_name or "student").split()[0] if (full_name or "").split() else "student"
    base = slugify(first).replace("-", "")[:15] or "student"
    for _ in range(30):
        candidate = f"{base}{random.randint(100, 999)}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
    return f"{base}{random.randint(1000, 9999)}"


def _generate_password():
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=8))


def create_student_account(lead):
    """Creates (and links) a student-role login for a Lead. No-op if already linked."""
    if lead.student_account_id:
        return lead.student_account

    name_parts = (lead.full_name or "").split()
    username = _generate_username(lead.full_name)
    raw_password = _generate_password()

    user = User(
        username=username,
        first_name=name_parts[0] if name_parts else "",
        last_name=" ".join(name_parts[1:]),
        role=User.Role.STUDENT,
        plain_password=raw_password,
    )
    user.set_password(raw_password)
    user.save()

    lead.student_account = user
    lead.save(update_fields=["student_account"])
    return user


def set_student_credentials(user, username=None, password=None):
    """Staff-driven edit of a student account's username/password, keeping plain_password in sync."""
    if username and username != user.username:
        user.username = username
    if password:
        user.set_password(password)
        user.plain_password = password
    user.save()
    return user
