from django import forms
from django.utils.text import slugify

from .models import FieldDefinition


class FieldDefinitionForm(forms.ModelForm):
    options_text = forms.CharField(
        label="Options",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "One option per line — only used for Dropdown / Checkboxes"}),
        help_text="One option per line.",
    )

    class Meta:
        model = FieldDefinition
        fields = [
            "target_model",
            "label",
            "key",
            "field_type",
            "options_text",
            "group",
            "order",
            "required",
            "show_on_dashboard_tally",
            "active",
        ]
        widgets = {"target_model": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["key"].required = False
        self.fields["key"].help_text = "Leave blank to auto-generate from the label."
        if self.instance and self.instance.pk:
            self.fields["options_text"].initial = "\n".join(self.instance.options or [])

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("key") and cleaned.get("label"):
            cleaned["key"] = slugify(cleaned["label"]).replace("-", "_")[:60]
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        text = self.cleaned_data.get("options_text", "")
        instance.options = [line.strip() for line in text.splitlines() if line.strip()]
        if commit:
            instance.save()
        return instance
