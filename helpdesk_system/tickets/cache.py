from django.core.cache import cache

# Cache keys
TICKET_LIST_KEY = "tickets:list:user:{user_id}"
TICKET_DETAIL_KEY = "tickets:detail:{ticket_id}"

# Cache timeout (5 minutes)
CACHE_TTL = 60 * 5


def get_ticket_list_cache_key(user):
    """Generate cache key for ticket list."""
    return TICKET_LIST_KEY.format(user_id=user.id if user.is_customer else "all")


def get_ticket_detail_cache_key(ticket_id):
    """Generate cache key for ticket detail."""
    return TICKET_DETAIL_KEY.format(ticket_id=ticket_id)


def invalidate_ticket_cache(ticket):
    """Invalidate all cache related to a ticket."""
    # Invalidate detail cache
    cache.delete(get_ticket_detail_cache_key(ticket.id))

    # Invalidate list caches (user-specific and all)
    cache.delete(TICKET_LIST_KEY.format(user_id=ticket.created_by.id))
    cache.delete(TICKET_LIST_KEY.format(user_id="all"))

    # If assigned, invalidate assigned user's cache too
    if ticket.assigned_to:
        cache.delete(TICKET_LIST_KEY.format(user_id=ticket.assigned_to.id))


def invalidate_all_ticket_list_cache():
    """Invalidate all ticket list caches using pattern."""
    cache.delete_pattern("tickets:list:*")
