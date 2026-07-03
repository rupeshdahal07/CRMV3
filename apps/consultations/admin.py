from django.contrib import admin

from .models import Consultation, ConsultationSlot, PostConsultationCall


@admin.register(ConsultationSlot)
class ConsultationSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "counselor", "status", "reserved_count")
    list_filter = ("status", "counselor")


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("lead", "slot", "status", "class_interest", "pmf_score")
    list_filter = ("status", "user_seriousness")
    raw_id_fields = ("slot", "lead", "recommended_cohort")


@admin.register(PostConsultationCall)
class PostConsultationCallAdmin(admin.ModelAdmin):
    list_display = ("lead", "call_date", "call_status", "cohort_interest", "called_by")
    list_filter = ("call_status", "cohort_interest")
    raw_id_fields = ("lead", "called_by", "preferred_cohort")
