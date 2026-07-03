"""Shared lookups for the student portal."""


def student_context(request):
    """The student's Lead, their active enrollment, and its cohort."""
    lead = getattr(request.user, "lead_profile", None)
    enrollment = None
    cohort = None
    if lead is not None:
        enrollment = lead.enrollments.select_related(
            "cohort", "cohort__assigned_teacher", "cohort__curriculum"
        ).first()
        cohort = enrollment.cohort if enrollment else None
    return lead, enrollment, cohort
