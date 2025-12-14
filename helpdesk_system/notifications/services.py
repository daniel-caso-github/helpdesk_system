from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class NotificationService:
    """Service for sending real-time notifications via WebSocket."""

    @staticmethod
    def _get_channel_layer():
        return get_channel_layer()

    @classmethod
    def notify_ticket_created(cls, ticket):
        """Notify all agents when a new ticket is created."""
        channel_layer = cls._get_channel_layer()

        data = {
            "type": "ticket_created",
            "ticket": {
                "id": ticket.id,
                "title": ticket.title,
                "priority": ticket.priority,
                "status": ticket.status,
                "created_by": ticket.created_by.username,
            },
            "message": f"New ticket #{ticket.id}: {ticket.title}",
        }

        async_to_sync(channel_layer.group_send)(
            "agents",
            {"type": "ticket_notification", "data": data},
        )

    @classmethod
    def notify_status_changed(cls, ticket, old_status):
        """Notify ticket creator when status changes."""
        channel_layer = cls._get_channel_layer()

        data = {
            "type": "status_changed",
            "ticket": {
                "id": ticket.id,
                "title": ticket.title,
                "old_status": old_status,
                "new_status": ticket.status,
            },
            "message": f"Ticket #{ticket.id} status changed to {ticket.get_status_display()}",
        }

        # Notify ticket creator
        async_to_sync(channel_layer.group_send)(
            f"user_{ticket.created_by.id}",
            {"type": "ticket_notification", "data": data},
        )

    @classmethod
    def notify_comment_added(cls, comment):
        """Notify relevant users when a comment is added."""
        channel_layer = cls._get_channel_layer()
        ticket = comment.ticket

        data = {
            "type": "comment_added",
            "ticket": {
                "id": ticket.id,
                "title": ticket.title,
            },
            "comment": {
                "id": comment.id,
                "author": comment.author.username,
                "content": comment.content[:100],  # Truncate for notification
            },
            "message": f"New comment on ticket #{ticket.id} by {comment.author.username}",
        }

        # Notify ticket creator if comment is from someone else
        if comment.author != ticket.created_by:
            async_to_sync(channel_layer.group_send)(
                f"user_{ticket.created_by.id}",
                {"type": "comment_notification", "data": data},
            )

        # Notify assigned agent if exists and is not the comment author
        if ticket.assigned_to and ticket.assigned_to != comment.author:
            async_to_sync(channel_layer.group_send)(
                f"user_{ticket.assigned_to.id}",
                {"type": "comment_notification", "data": data},
            )
