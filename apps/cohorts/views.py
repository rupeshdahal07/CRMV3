"""Cohort detail (roster + schedule) and curriculum detail."""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.core import permissions as perm

from .models import Cohort, Curriculum, DailyScore


@login_required
def cohort_detail(request, pk):
    cohort = get_object_or_404(Cohort, pk=pk)
    if not perm.can_access_cohort(request.user, cohort):
        return HttpResponseForbidden("You don't have access to this cohort.")
    can_edit_events = perm.role_of(request.user) == "admin" or (
        perm.role_of(request.user) == "teacher" and cohort.assigned_teacher_id == request.user.id
    )
    scored_days = set(
        DailyScore.objects.filter(enrollment__cohort=cohort).values_list("day_number", flat=True).distinct()
    )
    next_scoring_day = next(
        (d for d in range(1, cohort.total_days + 1) if d not in scored_days), cohort.total_days or 1
    )
    today = timezone.localdate()
    upcoming_events = cohort.events.filter(Q(date__gte=today) | Q(date__isnull=True))
    return render(
        request,
        "cohorts/cohort_detail.html",
        {
            "cohort": cohort,
            "enrollments": cohort.enrollments.select_related("lead").all(),
            "events": upcoming_events,
            "can_score": perm.can_score_cohort(request.user, cohort),
            "can_edit_cohort": perm.can_edit(request.user, "cohorts"),
            "can_edit_enrollments": perm.can_edit(request.user, "enrollments"),
            "can_edit_events": can_edit_events,
            "can_view_leads": perm.can_view(request.user, "leads"),
            "next_scoring_day": next_scoring_day,
        },
    )


@login_required
def curriculum_detail(request, pk):
    curriculum = get_object_or_404(Curriculum, pk=pk)
    return render(
        request,
        "cohorts/curriculum_detail.html",
        {
            "curriculum": curriculum,
            "chapters": curriculum.chapters.select_related("assigned_teacher").all(),
            "can_edit": perm.can_edit(request.user, "curriculum"),
        },
    )
