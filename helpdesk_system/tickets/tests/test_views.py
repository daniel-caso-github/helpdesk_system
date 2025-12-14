import pytest
from django.urls import reverse
from rest_framework import status

from helpdesk_system.tickets.models import Ticket
from helpdesk_system.users.tests.factories import CommentFactory
from helpdesk_system.users.tests.factories import TicketFactory


@pytest.mark.django_db
class TestTicketViewSet:
    def test_list_tickets_unauthenticated(self, api_client):
        url = reverse("api:ticket-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tickets_as_customer(self, customer_api_client, customer):
        # Create tickets for this customer
        TicketFactory.create_batch(3, created_by=customer)
        # Create tickets for another customer (should not be visible)
        TicketFactory.create_batch(2)

        url = reverse("api:ticket-list")
        response = customer_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3  # noqa: PLR2004

    def test_list_tickets_as_agent(self, agent_api_client, customer):
        # Create tickets for different customers
        TicketFactory.create_batch(5, created_by=customer)

        url = reverse("api:ticket-list")
        response = agent_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5  # noqa: PLR2004

    def test_create_ticket_as_customer(self, customer_api_client):
        url = reverse("api:ticket-list")
        data = {
            "title": "New Ticket",
            "description": "Description of the issue",
            "priority": "high",
        }
        response = customer_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "New Ticket"
        # Verify ticket was created with correct status
        ticket = Ticket.objects.get(id=response.data["id"])
        assert ticket.status == Ticket.Status.OPEN

    def test_retrieve_ticket(self, customer_api_client, customer):
        ticket = TicketFactory(created_by=customer)
        url = reverse("api:ticket-detail", kwargs={"pk": ticket.pk})
        response = customer_api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == ticket.id

    def test_customer_cannot_update_status(self, customer_api_client, customer):
        ticket = TicketFactory(created_by=customer)
        url = reverse("api:ticket-detail", kwargs={"pk": ticket.pk})
        data = {"status": "in_progress"}
        response = customer_api_client.patch(url, data)

        # Customer should not be able to update
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_agent_can_update_status(self, agent_api_client, customer):
        ticket = TicketFactory(created_by=customer)
        url = reverse("api:ticket-detail", kwargs={"pk": ticket.pk})
        data = {"status": "in_progress"}
        response = agent_api_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "in_progress"

    def test_filter_by_status(self, agent_api_client, customer):
        TicketFactory(created_by=customer, status=Ticket.Status.OPEN)
        TicketFactory(created_by=customer, status=Ticket.Status.OPEN)
        TicketFactory(created_by=customer, status=Ticket.Status.RESOLVED)

        url = reverse("api:ticket-list")
        response = agent_api_client.get(url, {"status": "open"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # noqa: PLR2004

    def test_filter_by_priority(self, agent_api_client, customer):
        TicketFactory(created_by=customer, priority=Ticket.Priority.URGENT)
        TicketFactory(created_by=customer, priority=Ticket.Priority.LOW)

        url = reverse("api:ticket-list")
        response = agent_api_client.get(url, {"priority": "urgent"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_search_tickets(self, agent_api_client, customer):
        TicketFactory(created_by=customer, title="Error in login page")
        TicketFactory(created_by=customer, title="Payment issue")

        url = reverse("api:ticket-list")
        response = agent_api_client.get(url, {"search": "login"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestCommentViewSet:
    def test_list_comments(self, customer_api_client, customer):
        ticket = TicketFactory(created_by=customer)
        CommentFactory.create_batch(3, ticket=ticket, author=customer)

        url = reverse("api:comment-list")
        response = customer_api_client.get(url, {"ticket": ticket.id})

        assert response.status_code == status.HTTP_200_OK
        # Response is paginated
        assert response.data["count"] == 3  # noqa: PLR2004
        assert len(response.data["results"]) == 3  # noqa: PLR2004

    def test_create_comment(self, customer_api_client, customer):
        ticket = TicketFactory(created_by=customer)
        url = reverse("api:comment-list")
        data = {
            "ticket": ticket.id,
            "content": "This is a comment",
        }
        response = customer_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "This is a comment"

    def test_agent_can_comment_on_any_ticket(self, agent_api_client):
        # Ticket created by another user
        ticket = TicketFactory()

        url = reverse("api:comment-list")
        data = {
            "ticket": ticket.id,
            "content": "Agent comment",
        }
        response = agent_api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
