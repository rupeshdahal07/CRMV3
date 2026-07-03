from django.urls import path

from . import views

urlpatterns = [
    path("cohorts/<int:cohort_id>/scoring/", views.cohort_scoring, name="cohort_scoring"),
    path("cohorts/<int:cohort_id>/scoring/<int:day_number>/", views.cohort_scoring, name="cohort_scoring"),
    path("cohorts/<int:cohort_id>/leaderboard/", views.cohort_leaderboard, name="cohort_leaderboard"),
]
