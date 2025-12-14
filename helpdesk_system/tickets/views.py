from django.core.cache import cache
from django.db.models import Count
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema_view
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.response import Response

from .cache import CACHE_TTL
from .cache import get_ticket_list_cache_key
from .cache import invalidate_ticket_cache
from .models import Comment
from .models import Ticket
from .permissions import CommentPermission
from .permissions import TicketPermission
from .serializers import CommentCreateSerializer
from .serializers import CommentSerializer
from .serializers import TicketCreateSerializer
from .serializers import TicketDetailSerializer
from .serializers import TicketListSerializer
from .serializers import TicketUpdateSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List tickets",
        description=(
            "Returns paginated list of tickets. "
            "Customers see only their own tickets, agents see all."
        ),
    ),
    create=extend_schema(
        summary="Create ticket",
        description=(
            "Create a new support ticket. "
            "The authenticated user becomes the ticket creator."
        ),
    ),
    retrieve=extend_schema(
        summary="Get ticket details",
        description="Returns ticket details including all comments.",
    ),
    update=extend_schema(
        summary="Update ticket",
        description=(
            "Update ticket fields. Only agents can change status and assignment."
        ),
    ),
    partial_update=extend_schema(
        summary="Partial update ticket",
        description="Partially update ticket fields.",
    ),
    destroy=extend_schema(
        summary="Delete ticket",
        description="Delete a ticket. Only agents can delete tickets.",
    ),
)
class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing support tickets.

    Provides CRUD operations with role-based access control:
    - **Customers**: Can create tickets and view/comment on their own tickets
    - **Agents**: Full access to all tickets, can change status and assign

    Supports filtering, search, and ordering:
    - Filter by: status, priority, assigned_to
    - Search in: title, description
    - Order by: created_at, updated_at, priority
    """

    permission_classes = [TicketPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
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

    def list(self, request, *args, **kwargs):
        """List tickets with caching."""
        # Only cache if no query params (filters, search, etc.)
        if not request.query_params:
            cache_key = get_ticket_list_cache_key(request.user)
            cached_data = cache.get(cache_key)

            if cached_data is not None:
                return Response(cached_data)

            response = super().list(request, *args, **kwargs)
            cache.set(cache_key, response.data, CACHE_TTL)
            return response

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        ticket = serializer.save(created_by=self.request.user)
        invalidate_ticket_cache(ticket)

    def perform_update(self, serializer):
        ticket = serializer.save()
        invalidate_ticket_cache(ticket)

    def perform_destroy(self, instance):
        invalidate_ticket_cache(instance)
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="List comments",
        description="Returns comments. Filter by ticket using ?ticket={id}",
    ),
    create=extend_schema(
        summary="Create comment",
        description="Add a comment to a ticket.",
    ),
    retrieve=extend_schema(
        summary="Get comment",
        description="Returns a single comment.",
    ),
    destroy=extend_schema(
        summary="Delete comment",
        description="Delete a comment.",
    ),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ticket comments.

    - **Customers**: Can view and create comments on their own tickets
    - **Agents**: Full access to all comments
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
        comment = serializer.save(author=self.request.user)
        # Invalidate ticket cache when comment is added
        invalidate_ticket_cache(comment.ticket)
