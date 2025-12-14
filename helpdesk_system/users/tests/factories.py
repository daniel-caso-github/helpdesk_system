from collections.abc import Sequence
from typing import Any

from factory import Faker
from factory import LazyAttribute
from factory import SubFactory
from factory import post_generation
from factory.django import DjangoModelFactory

from helpdesk_system.tickets.models import Comment
from helpdesk_system.tickets.models import Ticket
from helpdesk_system.users.models import User


class UserFactory(DjangoModelFactory[User]):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    role = User.Role.CUSTOMER

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Save again the instance if creating and at least one hook ran."""
        if create and results and not cls._meta.skip_postgeneration_save:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        model = User
        django_get_or_create = ["username"]


class TicketFactory(DjangoModelFactory[Ticket]):
    title = Faker("sentence", nb_words=5)
    description = Faker("paragraph")
    status = Ticket.Status.OPEN
    priority = Ticket.Priority.MEDIUM
    created_by = SubFactory(UserFactory, role=User.Role.CUSTOMER)
    assigned_to = None

    class Meta:
        model = Ticket


class CommentFactory(DjangoModelFactory[Comment]):
    ticket = SubFactory(TicketFactory)
    author = LazyAttribute(lambda obj: obj.ticket.created_by)
    content = Faker("paragraph")

    class Meta:
        model = Comment
