from django.urls import path

from . import views

urlpatterns = [
    path("consultation-slots/<int:pk>/profile/", views.consultation_slot_detail, name="consultation_slot_detail"),
    path("consultation-slots/<int:pk>/add-attendee/", views.consultation_slot_add_attendee, name="consultation_slot_add_attendee"),
]
