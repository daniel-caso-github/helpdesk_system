import pytest
from rest_framework.test import APIClient

from helpdesk_system.users.models import User
from helpdesk_system.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def customer(db) -> User:
    return UserFactory(role=User.Role.CUSTOMER)


@pytest.fixture
def agent(db) -> User:
    return UserFactory(role=User.Role.AGENT)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_api_client(customer, api_client):
    api_client.force_authenticate(user=customer)
    return api_client


@pytest.fixture
def agent_api_client(agent, api_client):
    api_client.force_authenticate(user=agent)
    return api_client
