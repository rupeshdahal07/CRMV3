from django import forms

from apps.accounts.models import User
from apps.cohorts.models import Cohort

from .models import Consultation, ConsultationSlot, PostConsultationCall


class ConsultationSlotForm(forms.ModelForm):
    class Meta:
        model = ConsultationSlot
        exclude = []
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only Teachers run consultation slots.
        self.fields["counselor"].queryset = User.objects.filter(
            role=User.Role.TEACHER
        ).order_by("username")


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        exclude = ["custom_data", "created_at"]
        widgets = {
            "preferred_class_time": forms.TimeInput(attrs={"type": "time"}),
            "preferred_class_start_date": forms.DateInput(attrs={"type": "date"}),
            "main_concern": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }


class PostConsultationCallForm(forms.ModelForm):
    class Meta:
        model = PostConsultationCall
        exclude = ["custom_data", "created_at"]
        widgets = {
            "call_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"type": "time"}),
            "next_followup_date": forms.DateInput(attrs={"type": "date"}),
            "consultation_feedback": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.preferred_cohort_id if self.instance else None
        qs = Cohort.objects.exclude(status="Finished")
        if current:
            qs = Cohort.objects.exclude(status="Finished") | Cohort.objects.filter(pk=current)
        self.fields["preferred_cohort"].queryset = qs.distinct()
