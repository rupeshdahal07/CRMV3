"""Daily scoring grid + cohort leaderboard."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.cohorts.models import Cohort, DailyScore
from apps.core import permissions as perm

from .services import save_scoring_day


@login_required
def cohort_scoring(request, cohort_id, day_number=1):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    if not perm.can_score_cohort(request.user, cohort):
        return HttpResponseForbidden("You can only score your own cohorts.")
    enrollments = cohort.enrollments.select_related("lead").all()
    day_number = max(1, min(int(day_number), cohort.total_days))
    week_number = (day_number - 1) // 6 + 1
    week_days = range((week_number - 1) * 6 + 1, week_number * 6 + 1)

    if request.method == "POST":
        save_scoring_day(request.user, cohort, enrollments, day_number, request.POST)
        return redirect("cohort_scoring", cohort_id=cohort.id, day_number=day_number)

    rows = []
    for enrollment in enrollments:
        score = DailyScore.objects.filter(enrollment=enrollment, day_number=day_number).first()
        rows.append({"enrollment": enrollment, "score": score})

    day_score_sample = DailyScore.objects.filter(enrollment__cohort=cohort, day_number=day_number).first()

    return render(
        request,
        "scoring/scoring.html",
        {
            "cohort": cohort,
            "day_number": day_number,
            "week_number": week_number,
            "week_days": week_days,
            "week_options": [(w, (w - 1) * 6 + 1) for w in range(1, cohort.total_weeks + 1)],
            "rows": rows,
            "day_date": day_score_sample.date if day_score_sample else None,
            "day_lesson": day_score_sample.lesson if day_score_sample else "",
            "day_asked_documentation": day_score_sample.asked_documentation if day_score_sample else "none",
            "day_completed": day_score_sample is not None,
        },
    )


@login_required
def cohort_leaderboard(request, cohort_id):
    cohort = get_object_or_404(Cohort, pk=cohort_id)
    if not perm.can_access_cohort(request.user, cohort):
        return HttpResponseForbidden("You don't have access to this cohort.")
    enrollments = list(cohort.enrollments.select_related("lead").all())
    enrollments.sort(key=lambda e: e.total_score, reverse=True)
    for i, e in enumerate(enrollments, start=1):
        e.rank = i
        e.top10 = i <= 10
    return render(request, "scoring/leaderboard.html", {"cohort": cohort, "enrollments": enrollments})
