import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Personal group for this user
        self.user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # Agents subscribe to the agents group
        if self.user.role == "agent":
            await self.channel_layer.group_add("agents", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

        if hasattr(self, "user") and self.user.is_authenticated:
            if self.user.role == "agent":
                await self.channel_layer.group_discard("agents", self.channel_name)

    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        # For now, we just echo back or handle ping/pong
        message_type = content.get("type", "")

        if message_type == "ping":
            await self.send_json({"type": "pong"})

    async def ticket_notification(self, event):
        """Send ticket notification to WebSocket."""
        await self.send_json(event["data"])

    async def comment_notification(self, event):
        """Send comment notification to WebSocket."""
        await self.send_json(event["data"])
