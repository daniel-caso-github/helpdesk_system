from django.db.models import Count
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Comment
from .models import Ticket
from .permissions import TicketPermission, CommentPermission
from .serializers import CommentCreateSerializer
from .serializers import CommentSerializer
from .serializers import TicketCreateSerializer
from .serializers import TicketDetailSerializer
from .serializers import TicketListSerializer
from .serializers import TicketUpdateSerializer


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tickets with role-based filtering.

    - Customers: only see their own tickets
    - Agents: see all tickets
    """

    permission_classes = [TicketPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            "created_by",
            "assigned_to",
        ).annotate(
            comments_count=Count("comments"),
            last_comment_at=Max("comments__created_at"),
        )

        # Customers only see their own tickets
        if self.request.user.is_customer:
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "create":
            return TicketCreateSerializer
        if self.action in ["update", "partial_update"]:
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comments.

    - Customers: only see comments on their tickets
    - Agents: see all comments
    """

    permission_classes = [CommentPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["ticket"]
    ordering = ["created_at"]

    def get_queryset(self):
        queryset = Comment.objects.select_related("author", "ticket")

        # Customers only see comments on their tickets
        if self.request.user.is_customer:
            queryset = queryset.filter(ticket__created_by=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
