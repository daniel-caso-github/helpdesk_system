from django.db.models.signals import post_save
from django.dispatch import receiver

from helpdesk_system.emails.tasks import send_comment_added_email
from helpdesk_system.emails.tasks import send_status_changed_email
from helpdesk_system.emails.tasks import send_ticket_created_email
from helpdesk_system.notifications.services import NotificationService

from .models import Comment
from .models import Ticket


@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """Handle ticket post-save signals."""
    if created:
        # New ticket created - notify agents
        send_ticket_created_email.delay(instance.id)
        NotificationService.notify_ticket_created(instance)
    elif instance.tracker.has_changed("status"):
        old_status = instance.tracker.previous("status")
        send_status_changed_email.delay(instance.id, old_status)
        NotificationService.notify_status_changed(instance, old_status)


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Handle comment post-save signals."""
    if created:
        send_comment_added_email.delay(instance.id)
        NotificationService.notify_comment_added(instance)
