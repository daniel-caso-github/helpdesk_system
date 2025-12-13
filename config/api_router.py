from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from helpdesk_system.tickets.views import TicketViewSet, CommentViewSet
from helpdesk_system.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)
router.register("tickets", TicketViewSet, basename="ticket")
router.register("comments", CommentViewSet, basename="comment")


app_name = "api"
urlpatterns = router.urls
