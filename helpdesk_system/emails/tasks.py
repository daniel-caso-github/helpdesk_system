
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def send_ticket_email(self, email_log_id: int):
    """Send email and update EmailLog status."""
    from .models import EmailLog

    try:
        email_log = EmailLog.objects.get(id=email_log_id)

        msg = EmailMultiAlternatives(
            subject=email_log.subject,
            body="Please view this email in an HTML-compatible email client.",
            to=[email_log.recipient],
        )
        msg.attach_alternative(email_log.body_html, "text/html")
        msg.send()

        email_log.status = EmailLog.Status.SENT
        email_log.sent_at = timezone.now()
        email_log.save(update_fields=["status", "sent_at"])

    except EmailLog.DoesNotExist:
        pass  # Email log was deleted
    except Exception as exc:
        email_log.status = EmailLog.Status.FAILED
        email_log.error_message = str(exc)
        email_log.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_ticket_created_email(ticket_id: int):
    """Send email notification when a ticket is created."""
    from helpdesk_system.tickets.models import Ticket
    from helpdesk_system.users.models import User

    from .models import EmailLog

    try:
        ticket = Ticket.objects.select_related("created_by").get(id=ticket_id)
    except Ticket.DoesNotExist:
        return

    # Notify all agents
    agents = User.objects.filter(role=User.Role.AGENT)

    for agent in agents:
        html_content = render_to_string(
            "emails/ticket_created.html",
            {
                "ticket": ticket,
                "recipient_name": agent.name or agent.username,
            },
        )

        email_log = EmailLog.objects.create(
            recipient=agent.email,
            subject=f"[Ticket #{ticket.id}] {ticket.title}",
            body_html=html_content,
            ticket=ticket,
        )

        send_ticket_email.delay(email_log.id)


@shared_task
def send_status_changed_email(ticket_id: int, old_status: str):
    """Send email notification when ticket status changes."""
    from helpdesk_system.tickets.models import Ticket

    from .models import EmailLog

    try:
        ticket = Ticket.objects.select_related("created_by").get(id=ticket_id)
    except Ticket.DoesNotExist:
        return

    # Notify ticket creator
    recipient = ticket.created_by

    html_content = render_to_string(
        "emails/status_changed.html",
        {
            "ticket": ticket,
            "old_status": old_status,
            "recipient_name": recipient.name or recipient.username,
        },
    )

    email_log = EmailLog.objects.create(
        recipient=recipient.email,
        subject=f"[Ticket #{ticket.id}] Status Updated",
        body_html=html_content,
        ticket=ticket,
    )

    send_ticket_email.delay(email_log.id)


@shared_task
def send_comment_added_email(comment_id: int):
    """Send email notification when a comment is added."""
    from helpdesk_system.tickets.models import Comment

    from .models import EmailLog

    try:
        comment = Comment.objects.select_related(
            "ticket",
            "ticket__created_by",
            "author",
        ).get(id=comment_id)
    except Comment.DoesNotExist:
        return

    ticket = comment.ticket

    # Notify ticket creator if comment is from someone else
    if comment.author != ticket.created_by:
        recipient = ticket.created_by

        html_content = render_to_string(
            "emails/comment_added.html",
            {
                "ticket": ticket,
                "comment": comment,
                "recipient_name": recipient.name or recipient.username,
            },
        )

        email_log = EmailLog.objects.create(
            recipient=recipient.email,
            subject=f"[Ticket #{ticket.id}] New Comment",
            body_html=html_content,
            ticket=ticket,
        )

        send_ticket_email.delay(email_log.id)
