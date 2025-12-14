import contextlib

from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "helpdesk_system.tickets"

    def ready(self):
        with contextlib.suppress(ImportError):
            import helpdesk_system.tickets.signals  # noqa: F401, PLC0415
