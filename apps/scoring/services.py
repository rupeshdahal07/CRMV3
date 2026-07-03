"""
Daily-scoring write logic, extracted from the view.

`save_scoring_day` applies a day's scores for every enrollment, runs the
absence auto-flag rule, raises follow-ups for newly-flagged students, and seeds
documentation status when the teacher asked in class.
"""

from django.utils import timezone

from apps.cohorts.models import DailyScore, Followup
from apps.leads.models import Lead


def save_scoring_day(user, cohort, enrollments, day_number, post):
    """Persist one scoring day from POST data. Mirrors the CRMV2 behaviour exactly."""
    saved_scores = []
    date = post.get("day_date") or None
    lesson = post.get("day_lesson", "")
    asked_documentation = post.get("day_asked_documentation", "none")

    for enrollment in enrollments:
        prefix = f"e{enrollment.id}_"
        status = post.get(prefix + "status", "")
        class_presence = post.get(prefix + "cp") or None
        effort = post.get(prefix + "ed") or None
        hw = post.get(prefix + "hw") or None
        note = post.get(prefix + "note", "")
        manual_needs_followup = bool(post.get(prefix + "needs_followup"))

        score, created = DailyScore.objects.get_or_create(enrollment=enrollment, day_number=day_number)
        was_flagged = score.needs_followup
        score.status = status
        score.class_presence = class_presence
        score.effort_discipline = effort
        score.hw_practice = hw
        score.note = note
        score.date = date
        score.lesson = lesson
        score.asked_documentation = asked_documentation
        score.needs_followup = manual_needs_followup
        score.scored_by = user
        saved_scores.append((score, created, was_flagged))

    # Auto-flag: absent while at least one cohort-mate was present that same day.
    any_present = any(s.status == "Present" for s, _, _ in saved_scores)
    if any_present:
        for score, _, _ in saved_scores:
            if score.status == "Absent":
                score.needs_followup = True

    for score, created, was_flagged in saved_scores:
        score.save()
        newly_flagged = score.needs_followup and (created or not was_flagged)
        if newly_flagged:
            Followup.objects.create(
                lead=score.enrollment.lead,
                enrollment=score.enrollment,
                followup_type="needs_attention",
                due_date=score.date or timezone.localdate(),
                remark=f"Day {day_number} scoring flagged a followup — status: {score.status or '—'}.",
                created_by=user,
            )

    if asked_documentation == "asked":
        # Initialize documentation status for anyone who doesn't have one yet — doesn't overwrite manual progress.
        Lead.objects.filter(id__in=[e.lead_id for e in enrollments], documentation_status="").update(
            documentation_status="asked_in_class"
        )
