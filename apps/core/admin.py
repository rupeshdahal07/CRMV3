from django.contrib import admin

from .models import FieldDefinition


@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ("label", "target_model", "field_type", "order", "required", "active")
    list_filter = ("target_model", "field_type", "active")
    search_fields = ("label", "key")
    ordering = ("target_model", "order")
