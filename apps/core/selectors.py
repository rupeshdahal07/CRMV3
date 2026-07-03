"""
Read-side query helpers shared by the dashboard and the generic list engine.

Selectors return data; they never mutate. Keeping them here keeps the views thin
and the DB access in one testable place.
"""

from django.utils import timezone

from apps.cohorts.models import Cohort, Enrollment, Followup
from apps.leads.models import CURIOSITY_CHOICES, IntakeTarget, Lead


def pending_followup_needs(queryset=None):
    """One row per lead — their most recent open needs-attention followup."""
    qs = (
        (queryset if queryset is not None else Followup.objects.all())
        .filter(followup_type="needs_attention", done=False, lead__isnull=False)
        .select_related("lead")
        .order_by("-due_date", "-created_at")
    )
    seen = set()
    result = []
    for f in qs:
        if f.lead_id in seen:
            continue
        seen.add(f.lead_id)
        result.append(f)
    return result


# Concern/topic boolean fields tallied on the dashboard.
CONCERN_FIELDS = [
    ("Fee Concern", "pain_fee"),
    ("Visa Rejected", "pain_visa_rejection"),
    ("Document Submitted", "pain_documentation"),
    ("Documentation Concern", "documentation_concern"),
    ("Accommodation Concern", "pain_accommodation"),
    ("Consultancy Doubts", "topic_consultancy"),
    ("Language School Concerns", "topic_language_school"),
    ("Job Concern", "topic_jobs"),
]


def dashboard_context(user, is_teacher):
    """Everything the admissions dashboard needs, scoped for teachers."""
    cohorts = Cohort.objects.all()
    enrollments = Enrollment.objects.select_related("lead", "cohort")
    followups = Followup.objects.select_related("lead", "enrollment__lead")
    if is_teacher:
        cohorts = cohorts.filter(assigned_teacher=user)
        enrollments = enrollments.filter(cohort__assigned_teacher=user)
        followups = followups.filter(enrollment__cohort__assigned_teacher=user)

    leads = Lead.objects.all()
    funnel = {
        "leads": leads.count(),
        "consultation_scheduled": leads.filter(call_status="Scheduled").count(),
        "consultation_completed": leads.filter(consultations__status="Completed").distinct().count(),
        "enrolled": Enrollment.objects.values("lead").distinct().count(),
    }

    topic_summary = [(label, leads.filter(**{key: True}).count()) for label, key in CONCERN_FIELDS]
    intake_summary = [(t.name, leads.filter(intake_target=t).count()) for t in IntakeTarget.objects.filter(active=True)]
    curiosity_summary = [(label, leads.filter(curiosity_level=value).count()) for value, label in CURIOSITY_CHOICES]

    needs_attention = [e for e in enrollments if e.needs_attention]
    today_followups = followups.filter(done=False, due_date__lte=timezone.localdate())
    followup_needed = pending_followup_needs(followups)

    return {
        "funnel": funnel,
        "topic_summary": topic_summary,
        "intake_summary": intake_summary,
        "curiosity_summary": curiosity_summary,
        "needs_attention": needs_attention,
        "today_followups": today_followups,
        "followup_needed": followup_needed,
        "cohorts": cohorts,
    }
