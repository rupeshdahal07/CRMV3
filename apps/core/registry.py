"""
Module registry — the data that drives the generic list/create/edit/delete engine.

Each entry maps a URL key (e.g. "leads") to its model, form, list columns,
searchable fields, filters, and optional parent/detail wiring. Adding a CRUD
screen is a config change here, not new view code.
"""

from django.db.models import Max

from apps.accounts.models import User
from apps.cohorts import forms as cohort_forms
from apps.cohorts import models as cohort_models
from apps.consultations import forms as consult_forms
from apps.consultations import models as consult_models
from apps.leads import forms as lead_forms
from apps.leads import models as lead_models

YES_NO_CHOICES = [("yes", "Yes"), ("no", "No")]


def _agents():
    return [(u.id, str(u)) for u in User.objects.filter(role__in=["support", "admin"])]


def _counselors():
    return [(u.id, str(u)) for u in User.objects.filter(role__in=["support", "admin", "teacher"])]


def _teachers():
    return [(u.id, str(u)) for u in User.objects.filter(role="teacher")]


def _cohorts():
    return [(c.id, str(c)) for c in cohort_models.Cohort.objects.all()]


def _slots():
    return [(s.id, str(s)) for s in consult_models.ConsultationSlot.objects.all()]


def _week_choices():
    max_weeks = cohort_models.Cohort.objects.aggregate(Max("total_weeks"))["total_weeks__max"] or 12
    return [(str(i), f"Week {i}") for i in range(1, max_weeks + 1)]


MODULES = {
    "leads": dict(
        model=lead_models.Lead,
        form=lead_forms.LeadForm,
        target_model="lead",
        title="Leads & Calls",
        list_columns=[
            ("User ID", "user_code", False),
            ("Name", "full_name", False),
            ("Phone", "phone", False),
            ("Stage", "current_stage", True),
            ("Needs Followup?", "needs_followup", False),
            ("Level", "level", False),
            ("Call Date", "call_date", False),
            ("Call Status", "call_status", True),
            ("Agent", "agent", False),
            ("Signup", "signup_date", False),
        ],
        search_fields=["user_code", "full_name", "phone"],
        has_detail=True,
        detail_url_name="lead_detail",
        filters=[
            {
                "param": "stage",
                "label": "Stage",
                "computed": "current_stage",
                "choices": [(s, s) for s in lead_models.Lead.STAGES],
            },
            {
                "param": "needs_followup",
                "label": "Needs Followup?",
                "computed": "needs_followup",
                "choices": YES_NO_CHOICES,
            },
            {"param": "level", "label": "Level", "field": "level", "choices": lead_models.LEVEL_CHOICES},
            {"param": "call_status", "label": "Call Status", "field": "call_status", "choices": lead_models.CALL_STATUS_CHOICES},
            {"param": "visa_category", "label": "Visa Category", "field": "visa_category", "choices": lead_models.VISA_CHOICES},
            {"param": "agent", "label": "Agent", "field": "agent_id", "choices_fn": _agents},
        ],
        default_sort="-created_at",
    ),
    "consultation-slots": dict(
        model=consult_models.ConsultationSlot,
        form=consult_forms.ConsultationSlotForm,
        target_model="consultation_slot",
        title="Consultation Slots",
        list_columns=[
            ("Date", "date", False),
            ("Time", "time", False),
            ("Counselor", "counselor", False),
            ("Status", "status", True),
            ("Reserved", "reserved_count", False),
            ("Link", "meeting_link", False),
        ],
        search_fields=[],
        has_detail=True,
        detail_url_name="consultation_slot_detail",
        filters=[
            {"param": "status", "label": "Status", "field": "status", "choices": consult_models.SLOT_STATUS_CHOICES},
            {"param": "counselor", "label": "Counselor", "field": "counselor_id", "choices_fn": _counselors},
            {"param": "date_from", "label": "From", "input": "date", "field": "date", "lookup": "gte"},
            {"param": "date_to", "label": "To", "input": "date", "field": "date", "lookup": "lte"},
        ],
    ),
    "consultations": dict(
        model=consult_models.Consultation,
        form=consult_forms.ConsultationForm,
        target_model="consultation",
        title="Consultation Reservations",
        list_columns=[
            ("Student", "lead", False),
            ("Slot", "slot", False),
            ("Status", "status", True),
            ("Class Interest?", "class_interest", False),
            ("PMF Score", "pmf_score", False),
        ],
        search_fields=["lead__full_name", "lead__user_code"],
        parent_field="lead",
        parent_model=lead_models.Lead,
        filters=[
            {"param": "status", "label": "Status", "field": "status", "choices": consult_models.ATTENDEE_STATUS_CHOICES},
            {"param": "slot", "label": "Slot", "field": "slot_id", "choices_fn": _slots},
            {"param": "user_seriousness", "label": "Seriousness", "field": "user_seriousness", "choices": consult_models.SERIOUSNESS_CHOICES},
        ],
    ),
    "post-consultation-calls": dict(
        model=consult_models.PostConsultationCall,
        form=consult_forms.PostConsultationCallForm,
        target_model="post_consultation_call",
        title="Post Consultation Calls",
        list_columns=[
            ("Student", "lead", False),
            ("Call Date", "call_date", False),
            ("Call Status", "call_status", True),
            ("Cohort Interest?", "cohort_interest", False),
            ("Preferred Cohort", "preferred_cohort", False),
            ("Called By", "called_by", False),
        ],
        search_fields=["lead__full_name", "lead__user_code"],
        parent_field="lead",
        parent_model=lead_models.Lead,
        filters=[
            {"param": "call_status", "label": "Call Status", "field": "call_status", "choices": lead_models.CALL_STATUS_CHOICES},
            {"param": "cohort_interest", "label": "Cohort Interest?", "field": "cohort_interest", "choices": YES_NO_CHOICES},
            {"param": "called_by", "label": "Called By", "field": "called_by_id", "choices_fn": _agents},
        ],
    ),
    "curriculum": dict(
        model=cohort_models.Curriculum,
        form=cohort_forms.CurriculumForm,
        target_model=None,
        title="Curriculum",
        list_columns=[("Name", "name", False), ("Level", "level", False), ("Chapters", "chapter_count", False), ("Active", "active", False)],
        search_fields=["name"],
        has_detail=True,
        detail_url_name="curriculum_detail",
        filters=[
            {"param": "level", "label": "Level", "field": "level", "choices": lead_models.LEVEL_CHOICES},
            {"param": "active", "label": "Active?", "field": "active", "choices": YES_NO_CHOICES},
        ],
    ),
    "curriculum-chapters": dict(
        model=cohort_models.CurriculumChapter,
        form=cohort_forms.CurriculumChapterForm,
        target_model=None,
        title="Curriculum Chapters",
        list_columns=[
            ("Curriculum", "curriculum", False),
            ("Week", "week_number", False),
            ("Day", "day_number", False),
            ("Chapter / Lesson", "title", False),
            ("Teacher", "assigned_teacher", False),
        ],
        search_fields=["title"],
        parent_field="curriculum",
        parent_model=cohort_models.Curriculum,
        filters=[{"param": "assigned_teacher", "label": "Teacher", "field": "assigned_teacher_id", "choices_fn": _teachers}],
    ),
    "cohorts": dict(
        model=cohort_models.Cohort,
        form=cohort_forms.CohortForm,
        target_model="cohort",
        title="Cohorts",
        list_columns=[
            ("Cohort", "name", False),
            ("Level", "level", False),
            ("Teacher", "assigned_teacher", False),
            ("Start Date", "start_date", False),
            ("Class Time", "class_time", False),
            ("Current Week", "current_week_display", False),
            ("Status", "status", True),
        ],
        search_fields=["code", "name"],
        has_detail=True,
        detail_url_name="cohort_detail",
        filters=[
            {"param": "status", "label": "Status", "field": "status", "choices": cohort_models.COHORT_STATUS_CHOICES},
            {"param": "level", "label": "Level", "field": "level", "choices": lead_models.LEVEL_CHOICES},
            {"param": "assigned_teacher", "label": "Teacher", "field": "assigned_teacher_id", "choices_fn": _teachers},
            {"param": "week", "label": "Current Week", "computed": "current_week", "choices_fn": _week_choices},
        ],
    ),
    "class-events": dict(
        model=cohort_models.ClassEvent,
        form=cohort_forms.ClassEventForm,
        target_model=None,
        title="Class Schedule",
        list_columns=[
            ("Type", "get_event_type_display", False),
            ("Status", "schedule_status", True),
            ("Date", "date", False),
            ("Time", "time", False),
            ("Details", "details", False),
            ("Join", "joining_link", False),
            ("Chapter", "related_chapter", False),
            ("Week/Day", "schedule_week_day_display", False),
        ],
        search_fields=["details", "notice"],
        parent_field="cohort",
        parent_model=cohort_models.Cohort,
        filters=[
            {"param": "event_type", "label": "Type", "field": "event_type", "choices": cohort_models.CLASS_EVENT_TYPE_CHOICES},
            {
                "param": "schedule_status",
                "label": "Status",
                "computed": "schedule_status",
                "choices": [("Upcoming", "Upcoming"), ("Completed", "Completed")],
            },
        ],
    ),
    "enrollments": dict(
        model=cohort_models.Enrollment,
        form=cohort_forms.EnrollmentForm,
        target_model="enrollment",
        title="Enrollments",
        list_columns=[
            ("Student", "lead", False),
            ("Cohort", "cohort", False),
            ("Enrolled", "enrolled_date", False),
            ("Nobigo Score", "total_score", False),
            ("Streak", "streak_score", False),
            ("Needs Attention?", "needs_attention", False),
            ("Ready for Next Week?", "auto_ready_for_next_week", False),
        ],
        search_fields=["lead__full_name", "lead__user_code"],
        parent_field="cohort",
        parent_model=cohort_models.Cohort,
        filters=[
            {"param": "cohort", "label": "Cohort", "field": "cohort_id", "choices_fn": _cohorts},
            {"param": "needs_attention", "label": "Needs Attention?", "computed": "needs_attention", "choices": YES_NO_CHOICES},
            {"param": "ready_for_next_week", "label": "Ready for Next Week?", "computed": "auto_ready_for_next_week", "choices": YES_NO_CHOICES},
            {"param": "followup_needed", "label": "Follow-up Needed?", "field": "followup_needed", "choices": YES_NO_CHOICES},
        ],
    ),
    "followups": dict(
        model=cohort_models.Followup,
        form=cohort_forms.FollowupForm,
        target_model="followup",
        title="Follow-ups",
        list_columns=[
            ("Lead", "lead", False),
            ("Enrollment", "enrollment", False),
            ("Type", "get_followup_type_display", True),
            ("Due", "due_date", False),
            ("Remark", "remark", False),
            ("Done?", "done", False),
        ],
        search_fields=["lead__full_name", "remark"],
        parent_field="lead",
        parent_model=lead_models.Lead,
        filters=[
            {"param": "followup_type", "label": "Type", "field": "followup_type", "choices": cohort_models.FOLLOWUP_TYPE_CHOICES},
            {"param": "done", "label": "Done?", "field": "done", "choices": YES_NO_CHOICES},
        ],
    ),
    "intake-targets": dict(
        model=lead_models.IntakeTarget,
        form=lead_forms.IntakeTargetForm,
        target_model=None,
        title="Intake Targets",
        list_columns=[("Name", "name", False), ("Active", "active", False)],
        search_fields=["name"],
    ),
}


def get_module(key):
    cfg = MODULES[key]
    cfg = dict(cfg, key=key)
    return cfg
