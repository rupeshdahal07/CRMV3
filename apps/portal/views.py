"""
Student Portal — a completely separate, mobile-first surface for enrolled
students to see their schedule, notices, leaderboard, and progress.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from apps.core import permissions as perm

from .selectors import student_context


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if perm.role_of(request.user) != "student":
            return HttpResponseForbidden("The Student Portal is only available to student accounts.")
        return view_func(request, *args, **kwargs)

    return wrapper


@student_required
def portal_home(request):
    lead, enrollment, cohort = student_context(request)
    today = timezone.localdate()

    upcoming_events = []
    notice_event = None
    days_until_next = None
    next_event = None
    if cohort is not None:
        upcoming_events = list(cohort.events.filter(date__gte=today).order_by("date", "time"))
        notice_event = next((e for e in upcoming_events if e.notice), None)
        next_event = upcoming_events[0] if upcoming_events else None
        if next_event and next_event.date:
            days_until_next = (next_event.date - today).days

    return render(
        request,
        "portal/home.html",
        {
            "lead": lead,
            "enrollment": enrollment,
            "cohort": cohort,
            "upcoming_events": upcoming_events,
            "notice_event": notice_event,
            "next_event": next_event,
            "days_until_next": days_until_next,
        },
    )


@student_required
def portal_notices(request):
    lead, enrollment, cohort = student_context(request)
    events_with_notices = []
    if cohort is not None:
        events_with_notices = list(cohort.events.exclude(notice="").order_by("-date", "-time"))
    today = timezone.localdate()
    return render(
        request,
        "portal/notices.html",
        {"cohort": cohort, "events_with_notices": events_with_notices, "today": today},
    )


@student_required
def portal_leaderboard(request):
    lead, enrollment, cohort = student_context(request)
    enrollments = []
    if cohort is not None:
        enrollments = list(cohort.enrollments.select_related("lead").all())
        enrollments.sort(key=lambda e: e.total_score, reverse=True)
        for i, e in enumerate(enrollments, start=1):
            e.rank = i
            e.top10 = i <= 10
    return render(
        request,
        "portal/leaderboard.html",
        {"cohort": cohort, "enrollments": enrollments, "me": enrollment},
    )


@student_required
def portal_progress(request):
    lead, enrollment, cohort = student_context(request)
    scores = []
    present_count = absent_count = 0
    if enrollment is not None:
        scores = list(enrollment.daily_scores.exclude(status="").order_by("-day_number"))
        present_count = sum(1 for s in scores if s.status == "Present")
        absent_count = sum(1 for s in scores if s.status == "Absent")
    return render(
        request,
        "portal/progress.html",
        {
            "lead": lead,
            "enrollment": enrollment,
            "cohort": cohort,
            "scores": scores,
            "present_count": present_count,
            "absent_count": absent_count,
        },
    )


@student_required
def portal_curriculum(request):
    lead, enrollment, cohort = student_context(request)
    chapters = []
    covered_days = set()
    if cohort is not None and cohort.curriculum_id:
        chapters = list(cohort.curriculum.chapters.select_related("assigned_teacher").all())
    if enrollment is not None:
        covered_days = set(enrollment.daily_scores.exclude(status="").values_list("day_number", flat=True))
    return render(
        request,
        "portal/curriculum.html",
        {"cohort": cohort, "chapters": chapters, "covered_days": covered_days},
    )
