from django import forms
from django.db.models import Q

from apps.accounts.models import User

from .models import IntakeTarget, Lead


class DurationSecondsWidget(forms.MultiWidget):
    """Minutes + seconds number inputs — a plain duration, no clock/AM-PM.

    The model still stores a single integer count of seconds.
    """

    def __init__(self, attrs=None):
        box = {"min": 0, "style": "width:110px; display:inline-block; margin-right:8px;"}
        widgets = [
            forms.NumberInput(attrs={**box, "placeholder": "Minutes"}),
            forms.NumberInput(attrs={**box, "max": 59, "placeholder": "Seconds"}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value in (None, ""):
            return [None, None]
        try:
            total = int(value)
        except (TypeError, ValueError):
            return [None, None]
        minutes, seconds = divmod(total, 60)
        return [minutes, seconds]


class DurationSecondsField(forms.MultiValueField):
    """Combines the minutes + seconds inputs into total seconds for storage."""

    widget = DurationSecondsWidget

    def __init__(self, **kwargs):
        fields = (
            forms.IntegerField(min_value=0),
            forms.IntegerField(min_value=0, max_value=59),
        )
        super().__init__(fields=fields, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        if not data_list:
            return None
        minutes, seconds = data_list
        if minutes in (None, "") and seconds in (None, ""):
            return None
        return (minutes or 0) * 60 + (seconds or 0)


class LeadForm(forms.ModelForm):
    call_duration_seconds = DurationSecondsField(required=False, label="Call duration (min : sec)")

    class Meta:
        model = Lead
        # student_account is auto-created here (first place a lead/student is made),
        # and documentation_status is managed from the lead detail page — so neither
        # is editable on this form.
        exclude = ["custom_data", "created_at", "updated_at", "student_account", "documentation_status"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "signup_date": forms.DateInput(attrs={"type": "date"}),
            "call_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.intake_target_id if self.instance else None
        qs = IntakeTarget.objects.filter(active=True)
        if current:
            qs = IntakeTarget.objects.filter(Q(active=True) | Q(pk=current))
        self.fields["intake_target"].queryset = qs

        # The agent handling a lead is always staff — never a student account.
        self.fields["agent"].queryset = User.objects.exclude(role=User.Role.STUDENT).order_by("username")


class IntakeTargetForm(forms.ModelForm):
    class Meta:
        model = IntakeTarget
        fields = ["name", "active"]
