"""
Shared model building blocks and the custom-fields engine.

`FieldDefinition` lets Admins add fields to any core form without a migration;
the values are stored in each record's `custom_data` JSON (see
`CustomFieldValueMixin`). The injection logic lives in `custom_fields.py`.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps. Use where both are wanted."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomFieldValueMixin(models.Model):
    """Storage for admin-defined custom field values (keyed by FieldDefinition.key)."""

    custom_data = models.JSONField(blank=True, default=dict)

    class Meta:
        abstract = True


class FieldDefinition(models.Model):
    """Lets Admins add custom fields to any core form without a migration."""

    class TargetModel(models.TextChoices):
        LEAD = "lead", "Lead"
        CONSULTATION_SLOT = "consultation_slot", "Consultation Slot"
        CONSULTATION = "consultation", "Consultation"
        POST_CONSULTATION_CALL = "post_consultation_call", "Post Consultation Call"
        COHORT = "cohort", "Cohort"
        ENROLLMENT = "enrollment", "Enrollment"
        DAILY_SCORE = "daily_score", "Daily Score"
        FOLLOWUP = "followup", "Follow-up"

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        TEXTAREA = "textarea", "Long text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        TIME = "time", "Time"
        BOOLEAN = "boolean", "Yes/No"
        DROPDOWN = "dropdown", "Dropdown"
        MULTISELECT = "multiselect", "Checkboxes (multi)"
        PHONE = "phone", "Phone"
        LINK = "link", "Link/URL"

    target_model = models.CharField(max_length=30, choices=TargetModel.choices)
    key = models.SlugField(max_length=60, help_text="Internal name, e.g. parent_contact")
    label = models.CharField(max_length=120)
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    options = models.JSONField(blank=True, default=list, help_text="For dropdown/checkboxes: list of option strings")
    group = models.CharField(max_length=80, blank=True, help_text="Section heading to show this field under")
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=False)
    show_on_dashboard_tally = models.BooleanField(
        default=False, help_text="Auto-tally this dropdown/checkbox field on the Dashboard"
    )
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("target_model", "key")
        ordering = ["target_model", "order", "id"]

    def __str__(self):
        return f"[{self.get_target_model_display()}] {self.label}"
