"""Root URL configuration — delegates to each domain app's urls module."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.accounts.forms import EmailOrUsernameAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth (shared, thin wrappers around Django's built-ins).
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=EmailOrUsernameAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Domain apps.
    path("", include("apps.core.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.leads.urls")),
    path("", include("apps.consultations.urls")),
    path("", include("apps.cohorts.urls")),
    path("", include("apps.scoring.urls")),
    path("portal/", include("apps.portal.urls")),
]
