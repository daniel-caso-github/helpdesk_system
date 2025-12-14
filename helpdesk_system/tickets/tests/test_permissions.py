import pytest
from rest_framework.test import APIRequestFactory

from helpdesk_system.tickets.permissions import TicketPermission
from helpdesk_system.users.tests.factories import TicketFactory


@pytest.mark.django_db
class TestTicketPermission:
    def test_agent_has_full_access(self, agent):
        permission = TicketPermission()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = agent

        class MockView:
            action = "destroy"

        assert permission.has_permission(request, MockView()) is True

    def test_customer_can_list_and_create(self, customer):
        permission = TicketPermission()
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = customer

        class MockView:
            action = "list"

        assert permission.has_permission(request, MockView()) is True

        MockView.action = "create"
        assert permission.has_permission(request, MockView()) is True

    def test_customer_cannot_destroy(self, customer):
        permission = TicketPermission()
        factory = APIRequestFactory()
        request = factory.delete("/")
        request.user = customer

        class MockView:
            action = "destroy"

        assert permission.has_permission(request, MockView()) is False

    def test_customer_can_access_own_ticket(self, customer):
        permission = TicketPermission()
        ticket = TicketFactory(created_by=customer)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = customer

        class MockView:
            action = "retrieve"

        assert permission.has_object_permission(request, MockView(), ticket) is True

    def test_customer_cannot_access_others_ticket(self, customer):
        permission = TicketPermission()
        ticket = TicketFactory()  # Created by another user
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = customer

        class MockView:
            action = "retrieve"

        assert permission.has_object_permission(request, MockView(), ticket) is False
