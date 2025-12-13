from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models

class User(AbstractUser):
    """
    Default custom user model for Helpdesk System.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        AGENT = "agent", _("Agent")

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    role = CharField(
        _("Role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    @property
    def is_customer(self) -> bool:
        return self.role == self.Role.CUSTOMER

    @property
    def is_agent(self) -> bool:
        return self.role == self.Role.AGENT
