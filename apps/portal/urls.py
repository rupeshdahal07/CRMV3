from django.urls import path

from . import views

urlpatterns = [
    path("", views.portal_home, name="portal_home"),
    path("notices/", views.portal_notices, name="portal_notices"),
    path("leaderboard/", views.portal_leaderboard, name="portal_leaderboard"),
    path("progress/", views.portal_progress, name="portal_progress"),
    path("curriculum/", views.portal_curriculum, name="portal_curriculum"),
]
