from helpdesk_system.notifications.services import NotificationService


class TestNotificationServiceMethods:
    """Test that NotificationService methods exist and are callable."""

    def test_notify_ticket_created_exists(self):
        assert hasattr(NotificationService, "notify_ticket_created")
        assert callable(NotificationService.notify_ticket_created)

    def test_notify_status_changed_exists(self):
        assert hasattr(NotificationService, "notify_status_changed")
        assert callable(NotificationService.notify_status_changed)

    def test_notify_comment_added_exists(self):
        assert hasattr(NotificationService, "notify_comment_added")
        assert callable(NotificationService.notify_comment_added)
