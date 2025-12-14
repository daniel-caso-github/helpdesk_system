from rest_framework import serializers

from helpdesk_system.users.models import User

from .models import Comment
from .models import Ticket


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user representation for nested serialization."""

    class Meta:
        model = User
        fields = ["id", "username", "name", "role"]
        read_only_fields = fields


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for ticket comments."""

    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "ticket", "author", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""

    class Meta:
        model = Comment
        fields = ["id", "ticket", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer for ticket list with aggregated data."""

    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    last_comment_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "created_by",
            "assigned_to",
            "comments_count",
            "last_comment_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer for ticket detail with nested comments."""

    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "created_by",
            "assigned_to",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tickets."""

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tickets (agents only)."""

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assigned_to",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
