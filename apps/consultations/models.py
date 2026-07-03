"""Consultation scheduling: bookable slots, per-lead reservations, and the post-consult call."""

from django.conf import settings
from django.db import models

from apps.core.models import CustomFieldValueMixin
from apps.leads.models import CALL_STATUS_CHOICES

SERIOUSNESS_CHOICES = [("High", "High"), ("Medium", "Medium"), ("Low", "Low"), ("Not Suitable", "Not Suitable")]

SLOT_STATUS_CHOICES = [
    ("Open", "Open"),
    ("Reserved", "Reserved"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
]

ATTENDEE_STATUS_CHOICES = [
    ("Reserved", "Reserved"),
    ("Completed", "Completed"),
    ("No Show", "No Show"),
    ("Cancelled", "Cancelled"),
]


class ConsultationSlot(models.Model):
    """A bookable consultation session — date/time/counselor/link — that multiple leads can be reserved into."""

    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="consultation_slots_run"
    )
    meeting_link = models.URLField("Link for Call", blank=True)
    status = models.CharField(max_length=20, choices=SLOT_STATUS_CHOICES, default="Open")
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.date} {self.time or ''} — {self.counselor or 'Unassigned'}".strip()

    @property
    def reserved_count(self):
        return self.attendees.count()


class Consultation(CustomFieldValueMixin):
    """One lead's reservation + outcome within a ConsultationSlot."""

    slot = models.ForeignKey(ConsultationSlot, on_delete=models.CASCADE, related_name="attendees")
    lead = models.ForeignKey("leads.Lead", on_delete=models.CASCADE, related_name="consultations")
    status = models.CharField(max_length=20, choices=ATTENDEE_STATUS_CHOICES, default="Reserved")
    user_seriousness = models.CharField(max_length=20, choices=SERIOUSNESS_CHOICES, blank=True)
    main_concern = models.TextField(blank=True)
    class_interest = models.BooleanField(default=False)
    preferred_class_time = models.TimeField(null=True, blank=True)
    preferred_class_start_date = models.DateField(null=True, blank=True)
    recommended_cohort = models.ForeignKey(
        "cohorts.Cohort", null=True, blank=True, on_delete=models.SET_NULL, related_name="recommended_for"
    )
    pmf_score = models.PositiveSmallIntegerField("PMF Score (1-5)", null=True, blank=True)
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("slot", "lead")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lead.full_name} in slot {self.slot}"


class PostConsultationCall(CustomFieldValueMixin):
    """Support's follow-up call after the consultation: get feedback, gauge cohort interest, and set up enrollment."""

    lead = models.ForeignKey("leads.Lead", on_delete=models.CASCADE, related_name="post_consultation_calls")
    call_date = models.DateField(null=True, blank=True)
    called_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="post_consultation_calls_made"
    )
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, blank=True)
    consultation_feedback = models.TextField("Consultation Feedback", blank=True)
    cohort_interest = models.BooleanField("Interested in Joining a Cohort?", default=False)
    preferred_cohort = models.ForeignKey(
        "cohorts.Cohort", null=True, blank=True, on_delete=models.SET_NULL, related_name="post_call_preferences"
    )
    preferred_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    next_followup_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-call_date"]

    def __str__(self):
        return f"Post-consultation call: {self.lead.full_name}"
