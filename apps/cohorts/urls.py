from django.urls import path

from . import views

urlpatterns = [
    path("cohorts/<int:pk>/profile/", views.cohort_detail, name="cohort_detail"),
    path("curriculum/<int:pk>/profile/", views.curriculum_detail, name="curriculum_detail"),
]
