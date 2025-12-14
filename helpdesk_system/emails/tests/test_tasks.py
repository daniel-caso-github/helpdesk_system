import pytest

from helpdesk_system.emails.models import EmailLog
from helpdesk_system.emails.tasks import send_ticket_email
from helpdesk_system.users.models import User
from helpdesk_system.users.tests.factories import TicketFactory
from helpdesk_system.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestSendTicketEmail:
    def test_send_ticket_email_invalid_id(self):
        # Should not raise exception for non-existent email log
        result = send_ticket_email(99999)
        assert result is None


@pytest.mark.django_db
class TestEmailLogCreation:
    def test_email_log_created_for_ticket(self):
        """Test that EmailLog entries can be created with ticket reference."""
        customer = UserFactory(role=User.Role.CUSTOMER)
        ticket = TicketFactory(created_by=customer)

        email_log = EmailLog.objects.create(
            recipient=customer.email,
            subject=f"Ticket #{ticket.id}",
            body_html="<p>Test</p>",
            ticket=ticket,
        )

        assert email_log.ticket == ticket
        assert email_log.recipient == customer.email
