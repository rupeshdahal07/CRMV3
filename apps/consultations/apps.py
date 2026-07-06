from django.apps import AppConfig


class ConsultationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.consultations"
    label = "consultations"
    verbose_name = "Consultations"

    def ready(self):
        from . import signals  # noqa: F401  (registers slot-status sync signals)
