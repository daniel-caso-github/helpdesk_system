from django.db import models
from django.utils.translation import gettext_lazy as _

from helpdesk_system import tickets


class EmailLog(models.Model):
    """Log of emails sent by the system."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    recipient = models.EmailField(_("Recipient"))
    subject = models.CharField(_("Subject"), max_length=255)
    body_html = models.TextField(_("Body HTML"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="email_logs",
        verbose_name=_("Ticket"),
        null=True,
        blank=True,
    )
    error_message = models.TextField(_("Error message"), blank=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Email Log")
        verbose_name_plural = _("Email Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.subject} -> {self.recipient} ({self.status})"
