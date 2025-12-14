from django.core.cache import cache
from django.db.models import Count
from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend
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


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tickets with role-based filtering.

    - Customers: only see their own tickets
    - Agents: see all tickets
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
        comment = serializer.save(author=self.request.user)
        # Invalidate ticket cache when comment is added
        invalidate_ticket_cache(comment.ticket)
