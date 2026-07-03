from django.urls import path

from . import views

urlpatterns = [
    path("leads/<int:pk>/profile/", views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/mark-ready/", views.lead_mark_ready, name="lead_mark_ready"),
    path("leads/<int:pk>/documentation-status/", views.lead_update_documentation_status, name="lead_update_documentation_status"),
    path("leads/<int:pk>/reserve-slot/", views.lead_reserve_slot, name="lead_reserve_slot"),
    path("leads/<int:pk>/reserve-slot/<int:slot_pk>/", views.lead_reserve_slot_confirm, name="lead_reserve_slot_confirm"),
    path("leads/<int:pk>/student-login/", views.lead_student_credentials, name="lead_student_credentials"),
    path("leads/<int:lead_id>/resolve-followup/", views.resolve_followup_need, name="resolve_followup_need"),
]
