import pytest

from helpdesk_system.tickets.models import Comment
from helpdesk_system.tickets.models import Ticket
from helpdesk_system.users.tests.factories import CommentFactory
from helpdesk_system.users.tests.factories import TicketFactory


@pytest.mark.django_db
class TestTicketModel:
    def test_create_ticket(self, customer):
        ticket = Ticket.objects.create(
            title="Test Ticket",
            description="Test Description",
            created_by=customer,
        )
        assert ticket.id is not None
        assert ticket.status == Ticket.Status.OPEN
        assert ticket.priority == Ticket.Priority.MEDIUM
        assert str(ticket) == f"#{ticket.pk} - Test Ticket"

    def test_ticket_factory(self):
        ticket = TicketFactory()
        assert ticket.id is not None
        assert ticket.created_by is not None

    def test_ticket_status_choices(self):
        assert Ticket.Status.OPEN == "open"
        assert Ticket.Status.IN_PROGRESS == "in_progress"
        assert Ticket.Status.RESOLVED == "resolved"
        assert Ticket.Status.CLOSED == "closed"

    def test_ticket_priority_choices(self):
        assert Ticket.Priority.LOW == "low"
        assert Ticket.Priority.MEDIUM == "medium"
        assert Ticket.Priority.HIGH == "high"
        assert Ticket.Priority.URGENT == "urgent"


@pytest.mark.django_db
class TestCommentModel:
    def test_create_comment(self, customer):
        ticket = TicketFactory(created_by=customer)
        comment = Comment.objects.create(
            ticket=ticket,
            author=customer,
            content="Test comment",
        )
        assert comment.id is not None
        assert comment.ticket == ticket
        assert str(comment) == f"Comment by {customer} on #{ticket.id}"

    def test_comment_factory(self):
        comment = CommentFactory()
        assert comment.id is not None
        assert comment.ticket is not None
        assert comment.author is not None
