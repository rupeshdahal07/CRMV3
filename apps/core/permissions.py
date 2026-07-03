"""
Role -> module access rules and teacher record-scoping.

Kept dependency-free (no model imports) so it can be used from anywhere,
including context processors and templates, without import cycles.
"""

# Which roles may see a module's records at all, and which may create/edit/delete
# them. Admin is implicitly allowed everywhere regardless of what's listed here.
MODULE_PERMS = {
    "leads": {"view": {"support"}, "edit": {"support"}},
    "consultation-slots": {"view": {"support", "teacher"}, "edit": {"support", "teacher"}},
    "consultations": {"view": {"support", "teacher"}, "edit": {"support", "teacher"}},
    "post-consultation-calls": {"view": {"support"}, "edit": {"support"}},
    "curriculum": {"view": {"support", "teacher"}, "edit": set()},
    "curriculum-chapters": {"view": {"support", "teacher"}, "edit": set()},
    "cohorts": {"view": {"support", "teacher"}, "edit": set()},
    "class-events": {"view": {"support", "teacher"}, "edit": {"teacher"}},
    "enrollments": {"view": {"support", "teacher"}, "edit": {"support", "teacher"}},
    "followups": {"view": {"support", "teacher"}, "edit": {"support"}},
    "intake-targets": {"view": set(), "edit": set()},
}


def role_of(user):
    if user.is_superuser:
        return "admin"
    return user.role


def can_view(user, module_key):
    role = role_of(user)
    if role == "admin":
        return True
    perm = MODULE_PERMS.get(module_key)
    if perm is None:
        return True
    return role in perm["view"]


def can_edit(user, module_key):
    role = role_of(user)
    if role == "admin":
        return True
    perm = MODULE_PERMS.get(module_key)
    if perm is None:
        return True
    return role in perm["edit"]


def scope_queryset(user, module_key, qs):
    """Teachers only ever see/touch their own cohorts and what hangs off them."""
    if role_of(user) != "teacher":
        return qs
    if module_key == "cohorts":
        return qs.filter(assigned_teacher=user)
    if module_key == "enrollments":
        return qs.filter(cohort__assigned_teacher=user)
    if module_key == "curriculum-chapters":
        return qs.filter(assigned_teacher=user)
    if module_key == "followups":
        return qs.filter(enrollment__cohort__assigned_teacher=user)
    if module_key == "consultation-slots":
        return qs.filter(counselor=user)
    if module_key == "consultations":
        return qs.filter(slot__counselor=user)
    if module_key == "class-events":
        return qs.filter(cohort__assigned_teacher=user)
    return qs


def owns_object(user, module_key, obj):
    """Object-level check for edit/delete: can this teacher touch this specific record?"""
    if role_of(user) != "teacher":
        return True
    if module_key == "cohorts":
        return obj.assigned_teacher_id == user.id
    if module_key == "enrollments":
        return obj.cohort.assigned_teacher_id == user.id
    if module_key == "curriculum-chapters":
        return obj.assigned_teacher_id == user.id
    if module_key == "followups":
        return bool(obj.enrollment) and obj.enrollment.cohort.assigned_teacher_id == user.id
    if module_key == "consultation-slots":
        return obj.counselor_id == user.id
    if module_key == "consultations":
        return obj.slot.counselor_id == user.id
    if module_key == "class-events":
        return obj.cohort.assigned_teacher_id == user.id
    return True


def can_access_cohort(user, cohort):
    role = role_of(user)
    if role in ("admin", "support"):
        return True
    if role == "teacher":
        return cohort.assigned_teacher_id == user.id
    return False


def can_score_cohort(user, cohort):
    role = role_of(user)
    if role == "admin":
        return True
    if role == "teacher":
        return cohort.assigned_teacher_id == user.id
    return False
