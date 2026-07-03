"""
Class management: curriculum, cohorts, the class schedule, enrollments, daily
scores, and follow-ups. This is the "after enrollment" half of the funnel and
holds the gamification logic (streaks, needs-attention, cohort weeks).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import CustomFieldValueMixin
from apps.leads.models import LEVEL_CHOICES

COHORT_STATUS_CHOICES = [
    ("Upcoming", "Upcoming"),
    ("Started", "Started"),
    ("On Hold", "On Hold"),
    ("Finished", "Finished"),
]

CLASS_EVENT_TYPE_CHOICES = [("class", "Class"), ("event", "Event")]

STATUS_CHOICES = [("Present", "Present"), ("Absent", "Absent")]
CLASS_PRESENCE_CHOICES = [(5, "5"), (4, "4"), (3, "3"), (2, "2"), (1, "1")]
HW_PRACTICE_CHOICES = [(5, "5"), (3, "3"), (1, "1"), (0, "0")]
ASKED_DOCUMENTATION_CHOICES = [("none", "None"), ("asked", "Asked Documentation")]

FOLLOWUP_TYPE_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("needs_attention", "Needs Attention"),
    ("general", "General"),
]


class Curriculum(models.Model):
    name = models.CharField(max_length=150)
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def chapter_count(self):
        return self.chapters.count()


class CurriculumChapter(models.Model):
    """One chapter/lesson on a specific day of a curriculum — assignable to a teacher per week."""

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name="chapters")
    week_number = models.PositiveSmallIntegerField(default=1)
    day_number = models.PositiveSmallIntegerField()
    title = models.CharField("Chapter / Lesson", max_length=200)
    notes = models.TextField(blank=True)
    assigned_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="curriculum_chapters"
    )

    class Meta:
        ordering = ["curriculum", "week_number", "day_number"]
        unique_together = ("curriculum", "day_number")

    def __str__(self):
        return f"{self.curriculum.name} W{self.week_number} D{self.day_number}: {self.title}"


class Cohort(CustomFieldValueMixin):
    code = models.CharField("Cohort ID", max_length=20, unique=True, help_text="e.g. C1")
    name = models.CharField("Cohort Name", max_length=80, blank=True, help_text="Auto pattern e.g. C1-260630-SB-19")
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, blank=True)
    start_date = models.DateField(null=True, blank=True)
    class_time = models.TimeField(null=True, blank=True)
    assigned_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="cohorts_taught"
    )
    curriculum = models.ForeignKey(Curriculum, null=True, blank=True, on_delete=models.SET_NULL, related_name="cohorts")
    whatsapp_group_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=COHORT_STATUS_CHOICES, default="Upcoming")
    total_weeks = models.PositiveSmallIntegerField(default=12, help_text="Curriculum length for this cohort — 6 class days per week.")

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name or self.code

    def save(self, *args, **kwargs):
        if not self.name and self.start_date:
            teacher_name = (
                self.assigned_teacher.get_full_name()
                if self.assigned_teacher_id and self.assigned_teacher.get_full_name()
                else ""
            )
            initials = "".join(p[0] for p in teacher_name.split()).upper()[:2]
            hour = self.class_time.hour if self.class_time else ""
            self.name = f"{self.code}-{self.start_date.strftime('%y%m%d')}-{initials}-{hour}"
        super().save(*args, **kwargs)

    @property
    def total_days(self):
        return self.total_weeks * 6

    @property
    def current_week(self):
        if not self.start_date:
            return 0
        elapsed_days = (timezone.localdate() - self.start_date).days
        if elapsed_days < 0:
            return 0
        return min(elapsed_days // 7 + 1, self.total_weeks)

    @property
    def current_week_display(self):
        week = self.current_week
        if week == 0:
            return "Not started"
        return f"Week {week} of {self.total_weeks}"


class ClassEvent(models.Model):
    """An upcoming class session or special event for a cohort — shown to students on the portal."""

    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=10, choices=CLASS_EVENT_TYPE_CHOICES, default="class")
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    related_chapter = models.ForeignKey(
        CurriculumChapter, null=True, blank=True, on_delete=models.SET_NULL, related_name="class_events",
        help_text="Optional — tag this event to a curriculum chapter, for reference only. Doesn't affect Daily Scoring.",
    )
    schedule_week = models.PositiveSmallIntegerField(
        "Week (optional)", null=True, blank=True,
        help_text="Optional — which week of the cohort this roughly corresponds to, for reference only.",
    )
    schedule_day = models.PositiveSmallIntegerField(
        "Day (optional)", null=True, blank=True,
        help_text="Optional — which day of that week, for reference only.",
    )
    joining_link = models.URLField(blank=True)
    passcode = models.CharField(max_length=50, blank=True, help_text="Leave blank if there's no passcode.")
    notice = models.TextField(
        "Notice", blank=True, help_text="Optional — shown highlighted to students on the Student Portal."
    )
    details = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Optional — internal notes, not shown to students.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="class_events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.cohort} — {self.date or 'no date'}"

    @property
    def schedule_week_day_display(self):
        if self.schedule_week and self.schedule_day:
            return f"Week {self.schedule_week}, Day {self.schedule_day}"
        if self.schedule_week:
            return f"Week {self.schedule_week}"
        return "—"

    @property
    def schedule_status(self):
        if not self.date:
            return "Upcoming"
        return "Completed" if self.date < timezone.localdate() else "Upcoming"


class Enrollment(CustomFieldValueMixin):
    """A student (lead) placed into a cohort — replaces the onboarding-to-class sheet."""

    lead = models.ForeignKey("leads.Lead", on_delete=models.CASCADE, related_name="enrollments")
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_date = models.DateField(null=True, blank=True)
    followup_needed = models.BooleanField(default=False)
    followup_outcome = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    ready_for_next_week = models.BooleanField(default=False, help_text="Manually confirmed once auto-eligible")

    class Meta:
        unique_together = ("lead", "cohort")
        ordering = ["-enrolled_date"]

    def __str__(self):
        return f"{self.lead.full_name} -> {self.cohort}"

    def daily_scores_qs(self):
        return self.daily_scores.all()

    @property
    def total_score(self):
        total = 0
        for s in self.daily_scores_qs():
            total += (s.class_presence or 0) + (s.effort_discipline or 0) + (s.hw_practice or 0)
        return total

    @property
    def present_count(self):
        return self.daily_scores_qs().filter(status="Present").count()

    @property
    def streak_score(self):
        n = self.present_count
        if n > 7:
            return 5
        if n >= 5:
            return 3
        if n >= 3:
            return 1
        return 0

    @property
    def needs_attention(self):
        # Flagged while this enrollment has an unresolved needs-attention follow-up.
        # Daily scoring raises these automatically (absence auto-flag / manual tick),
        # and resolving the follow-up on the Follow-ups page clears the flag here too.
        return self.followups.filter(followup_type="needs_attention", done=False).exists()

    @property
    def attention_reason(self):
        """Short 'where from' label for the cohort roster, e.g. the latest flag's remark."""
        f = self.followups.filter(followup_type="needs_attention", done=False).order_by("-due_date", "-created_at").first()
        return f.remark if f else ""

    @property
    def auto_ready_for_next_week(self):
        scores = list(self.daily_scores_qs())
        if not scores:
            return False
        return all(s.status == "Present" for s in scores)

    @property
    def paths_completed_pct(self):
        total_days = self.cohort.curriculum.chapters.count() if self.cohort.curriculum_id else self.cohort.total_days
        if not total_days:
            return 0
        done = self.daily_scores_qs().exclude(status="").count()
        return round(done / total_days * 100)


class DailyScore(CustomFieldValueMixin):
    """One student's score for one day of their cohort — replaces the big lesson tracker grid."""

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="daily_scores")
    day_number = models.PositiveSmallIntegerField()
    date = models.DateField(null=True, blank=True)
    lesson = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True)
    class_presence = models.PositiveSmallIntegerField(choices=CLASS_PRESENCE_CHOICES, null=True, blank=True)
    effort_discipline = models.PositiveSmallIntegerField(choices=CLASS_PRESENCE_CHOICES, null=True, blank=True)
    hw_practice = models.PositiveSmallIntegerField(choices=HW_PRACTICE_CHOICES, null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)
    needs_followup = models.BooleanField("Needs Followup?", default=False)
    asked_documentation = models.CharField(max_length=10, choices=ASKED_DOCUMENTATION_CHOICES, default="none", blank=True)
    scored_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="scores_given"
    )
    scored_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("enrollment", "day_number")
        ordering = ["enrollment", "day_number"]

    def __str__(self):
        return f"{self.enrollment.lead.full_name} Day {self.day_number}"

    @property
    def day_total(self):
        return (self.class_presence or 0) + (self.effort_discipline or 0) + (self.hw_practice or 0)


class Followup(CustomFieldValueMixin):
    lead = models.ForeignKey("leads.Lead", null=True, blank=True, on_delete=models.CASCADE, related_name="followups")
    enrollment = models.ForeignKey(Enrollment, null=True, blank=True, on_delete=models.CASCADE, related_name="followups")
    followup_type = models.CharField(max_length=20, choices=FOLLOWUP_TYPE_CHOICES, default="general")
    due_date = models.DateField(null=True, blank=True)
    remark = models.TextField(blank=True)
    done = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="followups_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["done", "due_date"]

    def __str__(self):
        who = self.lead.full_name if self.lead else (self.enrollment.lead.full_name if self.enrollment else "?")
        return f"Follow-up: {who} ({self.due_date})"
