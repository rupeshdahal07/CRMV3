from django.contrib import admin

from .models import IntakeTarget, Lead


@admin.register(IntakeTarget)
class IntakeTargetAdmin(admin.ModelAdmin):
    list_display = ("name", "active")
    list_filter = ("active",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("user_code", "full_name", "phone", "level", "call_status", "agent", "created_at")
    list_filter = ("level", "call_status", "visa_category", "ready_for_consultation")
    search_fields = ("user_code", "full_name", "phone")
    raw_id_fields = ("student_account", "agent", "intake_target")
