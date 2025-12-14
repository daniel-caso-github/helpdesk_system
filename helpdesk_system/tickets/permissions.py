from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """Check if user is a customer."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_customer


class IsAgent(permissions.BasePermission):
    """Check if user is an agent."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_agent


class TicketPermission(permissions.BasePermission):
    """
    Custom permission for tickets.

    - Customers: can create tickets, view/comment on their own
    - Agents: full access to all tickets
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Agents have full access
        if request.user.is_agent:
            return True

        # Customers can list, create, retrieve
        return view.action in ["list", "create", "retrieve"]

    def has_object_permission(self, request, view, obj):
        # Agents have full access
        if request.user.is_agent:
            return True

        # Customers can only access their own tickets
        return obj.created_by == request.user


class CommentPermission(permissions.BasePermission):
    """
    Custom permission for comments.

    - Customers: can comment on their own tickets
    - Agents: full access
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Agents have full access
        if request.user.is_agent:
            return True

        # Customers can list, create, retrieve
        return view.action in ["list", "create", "retrieve"]

    def has_object_permission(self, request, view, obj):
        # Agents have full access
        if request.user.is_agent:
            return True

        # Customers can only access comments on their tickets
        return obj.ticket.created_by == request.user
