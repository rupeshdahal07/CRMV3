from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Generic CRUD engine.
    path("m/<str:module_key>/", views.record_list, name="record_list"),
    path("m/<str:module_key>/new/", views.record_create, name="record_create"),
    path("m/<str:module_key>/<int:pk>/edit/", views.record_edit, name="record_edit"),
    path("m/<str:module_key>/<int:pk>/delete/", views.record_delete, name="record_delete"),
    # Custom field management.
    path("fields/", views.manage_fields, name="manage_fields_default"),
    path("fields/<str:target_model>/", views.manage_fields, name="manage_fields"),
    path("fields/<str:target_model>/new/", views.field_create, name="field_create"),
    path("fields/edit/<int:pk>/", views.field_edit, name="field_edit"),
    path("fields/delete/<int:pk>/", views.field_delete, name="field_delete"),
    path("fields/move/<int:pk>/<str:direction>/", views.field_move, name="field_move"),
]
