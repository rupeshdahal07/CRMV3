"""
Lead + admissions choices.

`Lead` is one row per prospective student and the spine of the whole funnel.
Many choice lists live here because they're first defined on the Lead form and
reused by later stages (consultations, cohorts).
"""

from django.conf import settings
from django.db import models

from apps.core.models import CustomFieldValueMixin

# --- Choice lists (shared across the funnel) --------------------------------- #
LEVEL_CHOICES = [
    ("Absolute beginner", "Absolute beginner"),
    ("N5", "N5"),
    ("N4", "N4"),
    ("N3", "N3"),
    ("N2", "N2"),
    ("N1", "N1"),
    ("None", "None"),
]

HIRAGANA_CHOICES = [
    ("None", "None"),
    ("Hiragana only", "Hiragana only"),
    ("Katakana only", "Katakana only"),
    ("Both", "Both"),
    ("Fluent", "Fluent"),
]

SKILL_FOCUS_CHOICES = [
    ("Vocab", "Vocab"),
    ("Grammar", "Grammar"),
    ("Kanji", "Kanji"),
    ("Listening & Speaking", "Listening & Speaking"),
    ("Exam Preparation", "Exam Preparation"),
]

JOURNEY_PROGRESS_CHOICES = [
    ("self_study_starting", "Just started learning by myself at home"),
    ("exploring_consultancy", "Exploring consultancies"),
    ("just_joined_consultancy", "Just joined a consultancy"),
    ("joined_not_satisfied", "Joined a consultancy, but not satisfied"),
    ("joined_satisfied", "Joined a consultancy and satisfied"),
]

WHY_LEARN_JAPANESE_CHOICES = [
    ("study", "To Study in Japan (Student)"),
    ("work", "To Work in Japan (Working or SSW)"),
    ("dependent_visa", "Dependent Visa (Family Reunification)"),
    ("travel", "Travel to Japan (Sightseeing)"),
    ("personal_interest", "Personal Interest (Anime, Culture, Language)"),
]

SURVEY_LANGUAGE_CHOICES = [("NP", "Nepali (NP)"), ("JP", "Japanese (JP)"), ("EN", "English (EN)")]

VISA_CHOICES = [
    ("SSW", "SSW"),
    ("Student Visa", "Student Visa"),
    ("Working Visa", "Working Visa"),
    ("Dependent", "Dependent"),
    ("Not Decided Yet", "Not Decided Yet"),
    ("Visit Visa", "Visit Visa"),
    ("TITP visa", "TITP visa"),
]

CALL_STATUS_CHOICES = [
    ("Scheduled", "Scheduled"),
    ("Follow-up Needed", "Follow-up Needed"),
    ("Not Interested", "Not Interested"),
    ("No Answer", "No Answer"),
    ("Completed", "Completed"),
    ("Rescheduled", "Rescheduled"),
]

PREFERRED_LANGUAGE_CHOICES = [("Nepali", "Nepali"), ("English", "English")]

CURIOSITY_CHOICES = [("High", "High"), ("Medium", "Medium"), ("Low", "Low"), ("None", "None")]

DOCUMENTATION_STATUS_CHOICES = [
    ("asked_in_class", "Asked in Class (Next Followup Call)"),
    ("ready", "Ready for Documentation"),
    ("received", "Documentation Received Successfully"),
]


class IntakeTarget(models.Model):
    """Editable list of intake targets — managed by Admins, offered as a dropdown on the Lead form."""

    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Lead(CustomFieldValueMixin):
    """One row per prospective student — replaces the Call Tracker + Consultation sheets."""

    user_code = models.CharField("User ID", max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    signup_date = models.DateField(null=True, blank=True)
    student_account = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="lead_profile"
    )

    why_learn_japanese = models.CharField(
        "Why do you want to learn Japanese?", max_length=30, choices=WHY_LEARN_JAPANESE_CHOICES, blank=True
    )
    journey_progress = models.CharField(
        "How far are you on learning Japanese?", max_length=30, choices=JOURNEY_PROGRESS_CHOICES, blank=True
    )
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, blank=True)
    hiragana_katakana = models.CharField("Hiragana & Katakana familiarity", max_length=30, choices=HIRAGANA_CHOICES, blank=True)
    skill_focus = models.CharField(max_length=20, choices=SKILL_FOCUS_CHOICES, blank=True)
    survey_language = models.CharField(max_length=5, choices=SURVEY_LANGUAGE_CHOICES, blank=True)
    visa_category = models.CharField(max_length=30, choices=VISA_CHOICES, blank=True)

    already_in_consultancy = models.BooleanField(default=False)
    planning_join_consultancy = models.BooleanField(default=False)

    intake_target = models.ForeignKey(IntakeTarget, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    pain_fee = models.BooleanField("Fee Concern?", default=False)
    pain_visa_rejection = models.BooleanField("Visa Rejected?", default=False)
    pain_documentation = models.BooleanField("Document Submitted?", default=False)
    documentation_concern = models.BooleanField("Documentation Concern?", default=False)
    pain_accommodation = models.BooleanField("Accommodation Concern?", default=False)
    pain_other = models.CharField("Other concern", max_length=200, blank=True)

    topic_consultancy = models.BooleanField("Consultancy Doubts?", default=False)
    topic_language_school = models.BooleanField("Language School Concerns?", default=False)
    topic_jobs = models.BooleanField("Job Concern?", default=False)
    topic_other = models.CharField("Other topic", max_length=200, blank=True)

    curiosity_level = models.CharField("Curiosity to Know", max_length=10, choices=CURIOSITY_CHOICES, blank=True)
    curiosity_note = models.CharField("Curiosity Note", max_length=300, blank=True)

    call_date = models.DateField("Call Date", null=True, blank=True)
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES, blank=True)
    preferred_call_language = models.CharField(max_length=10, choices=PREFERRED_LANGUAGE_CHOICES, blank=True)
    call_duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads_handled"
    )
    notes = models.TextField(blank=True)

    ready_for_consultation = models.BooleanField("Ready for Consultation?", default=False)
    visa_interest = models.BooleanField("Interested in Visa Application (through us)?", default=False)
    documentation_status = models.CharField(
        "Documentation Process", max_length=20, choices=DOCUMENTATION_STATUS_CHOICES, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.user_code})"

    STAGES = [
        "Signed Up",
        "Called",
        "Ready for Consultation",
        "Consultation Reserved",
        "Consultation Completed",
        "Post Consultation Call",
        "Enrolled in Cohort",
        "Active in Class",
        "Completed Program",
    ]

    @property
    def current_stage(self):
        enrollments = list(self.enrollments.select_related("cohort").all())
        if any(e.cohort.status == "Finished" for e in enrollments):
            return "Completed Program"
        if any(e.daily_scores.exists() for e in enrollments):
            return "Active in Class"
        if enrollments:
            return "Enrolled in Cohort"

        if self.post_consultation_calls.exists():
            return "Post Consultation Call"

        consultations = list(self.consultations.all())
        if any(c.status == "Completed" for c in consultations):
            return "Consultation Completed"
        if any(c.status == "Reserved" for c in consultations):
            return "Consultation Reserved"

        if self.ready_for_consultation:
            return "Ready for Consultation"
        if self.call_status:
            return "Called"
        return "Signed Up"

    @property
    def stage_index(self):
        return self.STAGES.index(self.current_stage)

    @property
    def needs_followup(self):
        return self.followups.filter(followup_type="needs_attention", done=False).exists()
