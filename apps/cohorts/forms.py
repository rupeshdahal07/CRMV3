from django import forms

from apps.accounts.models import User

from .models import Cohort, ClassEvent, Curriculum, CurriculumChapter, Enrollment, Followup


class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ["name", "level", "description", "active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class CurriculumChapterForm(forms.ModelForm):
    class Meta:
        model = CurriculumChapter
        fields = ["curriculum", "week_number", "day_number", "title", "assigned_teacher", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class CohortForm(forms.ModelForm):
    class Meta:
        model = Cohort
        exclude = ["custom_data", "name"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "class_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A cohort can only be assigned to a Teacher.
        self.fields["assigned_teacher"].queryset = User.objects.filter(
            role=User.Role.TEACHER
        ).order_by("username")


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        exclude = ["custom_data"]
        widgets = {
            "enrolled_date": forms.DateInput(attrs={"type": "date"}),
            "followup_outcome": forms.Textarea(attrs={"rows": 2}),
            "remarks": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = self.instance.cohort_id if self.instance else None
        qs = Cohort.objects.exclude(status="Finished")
        if current:
            qs = Cohort.objects.exclude(status="Finished") | Cohort.objects.filter(pk=current)
        self.fields["cohort"].queryset = qs.distinct()
        self.fields["cohort"].help_text = (
            "Only cohorts that aren't Finished are offered here — an available cohort to place this student into."
        )

    def clean_lead(self):
        lead = self.cleaned_data["lead"]
        existing = Enrollment.objects.filter(lead=lead)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError(
                "This student is already enrolled in a cohort — only one active enrollment is allowed at a time."
            )
        return lead


class ClassEventForm(forms.ModelForm):
    class Meta:
        model = ClassEvent
        exclude = ["created_by", "created_at"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
            "notice": forms.Textarea(attrs={"rows": 2}),
            "details": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cohort = None
        if self.instance and self.instance.cohort_id:
            cohort = self.instance.cohort
        else:
            cohort_id = self.initial.get("cohort") or (self.data.get("cohort") if self.data else None)
            if cohort_id:
                cohort = Cohort.objects.filter(pk=cohort_id).first()

        if cohort and cohort.curriculum_id:
            self.fields["related_chapter"].queryset = cohort.curriculum.chapters.all()
        else:
            self.fields["related_chapter"].queryset = CurriculumChapter.objects.none()
        self.fields["related_chapter"].required = False
        self.fields["related_chapter"].help_text = "Optional — for reference only, doesn't affect Daily Scoring."

        total_weeks = cohort.total_weeks if cohort else 12
        self.fields["schedule_week"] = forms.TypedChoiceField(
            label="Week (optional)", required=False, coerce=int, empty_value=None,
            choices=[("", "—")] + [(w, f"Week {w}") for w in range(1, total_weeks + 1)],
            help_text="Optional — for reference only, doesn't affect Daily Scoring.",
        )
        self.fields["schedule_day"] = forms.TypedChoiceField(
            label="Day (optional)", required=False, coerce=int, empty_value=None,
            choices=[("", "—")] + [(d, f"Day {d}") for d in range(1, 7)],
            help_text="Optional — day within that week, for reference only.",
        )
        if self.instance and self.instance.pk:
            self.initial["schedule_week"] = self.instance.schedule_week
            self.initial["schedule_day"] = self.instance.schedule_day


class FollowupForm(forms.ModelForm):
    class Meta:
        model = Followup
        exclude = ["custom_data", "created_at", "created_by"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "remark": forms.Textarea(attrs={"rows": 2}),
        }
