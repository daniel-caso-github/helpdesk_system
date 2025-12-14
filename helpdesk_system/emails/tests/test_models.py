import pytest

from helpdesk_system.emails.models import EmailLog


@pytest.mark.django_db
class TestEmailLogModel:
    def test_create_email_log(self):
        email_log = EmailLog.objects.create(
            recipient="test@example.com",
            subject="Test Subject",
            body_html="<p>Test Body</p>",
        )

        assert email_log.id is not None
        assert email_log.status == EmailLog.Status.PENDING
        assert str(email_log) == "Test Subject -> test@example.com (pending)"

    def test_email_log_status_choices(self):
        assert EmailLog.Status.PENDING == "pending"
        assert EmailLog.Status.SENT == "sent"
        assert EmailLog.Status.FAILED == "failed"

    def test_email_log_update_status(self):
        email_log = EmailLog.objects.create(
            recipient="test@example.com",
            subject="Test",
            body_html="Body",
        )

        email_log.status = EmailLog.Status.SENT
        email_log.save()

        email_log.refresh_from_db()
        assert email_log.status == EmailLog.Status.SENT
