from django.contrib import admin

from .models import (
    Cohort,
    ClassEvent,
    Curriculum,
    CurriculumChapter,
    DailyScore,
    Enrollment,
    Followup,
)


class CurriculumChapterInline(admin.TabularInline):
    model = CurriculumChapter
    extra = 0


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "chapter_count", "active")
    list_filter = ("level", "active")
    inlines = [CurriculumChapterInline]


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "level", "assigned_teacher", "status", "current_week_display")
    list_filter = ("status", "level", "assigned_teacher")
    search_fields = ("code", "name")


@admin.register(ClassEvent)
class ClassEventAdmin(admin.ModelAdmin):
    list_display = ("cohort", "event_type", "date", "time", "schedule_status")
    list_filter = ("event_type", "cohort")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("lead", "cohort", "enrolled_date", "total_score", "needs_attention")
    list_filter = ("cohort", "followup_needed")
    raw_id_fields = ("lead", "cohort")


@admin.register(DailyScore)
class DailyScoreAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "day_number", "date", "status", "day_total", "needs_followup")
    list_filter = ("status", "needs_followup")
    raw_id_fields = ("enrollment", "scored_by")


@admin.register(Followup)
class FollowupAdmin(admin.ModelAdmin):
    list_display = ("__str__", "followup_type", "due_date", "done")
    list_filter = ("followup_type", "done")
    raw_id_fields = ("lead", "enrollment", "created_by")
