"""
Custom-field injection.

`inject_custom_fields(FormClass, target_model)` returns a form subclass with the
active `FieldDefinition` fields appended, reading/writing them from/to the
instance's `custom_data` JSON. Used by the generic CRUD engine (`core.views`).
"""

from django import forms

from .models import FieldDefinition


def inject_custom_fields(form_class, target_model):
    defs = list(FieldDefinition.objects.filter(target_model=target_model, active=True))
    if not defs:
        return form_class

    extra_fields = {}
    for d in defs:
        field_name = f"cf_{d.key}"
        opts = [(o, o) for o in (d.options or [])]
        if d.field_type == FieldDefinition.FieldType.TEXTAREA:
            field = forms.CharField(label=d.label, required=d.required, widget=forms.Textarea(attrs={"rows": 2}))
        elif d.field_type == FieldDefinition.FieldType.NUMBER:
            field = forms.FloatField(label=d.label, required=d.required)
        elif d.field_type == FieldDefinition.FieldType.DATE:
            field = forms.DateField(label=d.label, required=d.required, widget=forms.DateInput(attrs={"type": "date"}))
        elif d.field_type == FieldDefinition.FieldType.TIME:
            field = forms.TimeField(label=d.label, required=d.required, widget=forms.TimeInput(attrs={"type": "time"}))
        elif d.field_type == FieldDefinition.FieldType.BOOLEAN:
            field = forms.BooleanField(label=d.label, required=False)
        elif d.field_type == FieldDefinition.FieldType.DROPDOWN:
            field = forms.ChoiceField(label=d.label, required=d.required, choices=[("", "—")] + opts)
        elif d.field_type == FieldDefinition.FieldType.MULTISELECT:
            field = forms.MultipleChoiceField(
                label=d.label, required=d.required, choices=opts, widget=forms.CheckboxSelectMultiple
            )
        elif d.field_type == FieldDefinition.FieldType.LINK:
            field = forms.URLField(label=d.label, required=d.required)
        elif d.field_type == FieldDefinition.FieldType.PHONE:
            field = forms.CharField(label=d.label, required=d.required)
        else:
            field = forms.CharField(label=d.label, required=d.required)
        field.group = d.group or "Custom Fields"
        extra_fields[field_name] = field

    class DynamicForm(form_class):
        def __init__(self, *args, **kwargs):
            instance = kwargs.get("instance")
            super().__init__(*args, **kwargs)
            for name, field in extra_fields.items():
                self.fields[name] = field
            if instance is not None and instance.pk:
                for d in defs:
                    self.initial[f"cf_{d.key}"] = instance.custom_data.get(d.key)

        def save(self, commit=True):
            instance = super().save(commit=False)
            data = dict(instance.custom_data or {})
            for d in defs:
                data[d.key] = self.cleaned_data.get(f"cf_{d.key}")
            instance.custom_data = data
            if commit:
                instance.save()
                self.save_m2m()
            return instance

    DynamicForm.__name__ = form_class.__name__
    return DynamicForm
