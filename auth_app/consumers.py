import json
from channels.generic.websocket import AsyncWebsocketConsumer

from auth_app.models import User

class AdminNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect to the WebSocket group for admin notifications."""
        self.group_name = "admin_notifications"
        if self.scope["user"].is_authenticated and self.scope["user"].role == User.SYSTEM_ADMIN:
            await self.channel_layer.group_add(self.admin_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        """Remove connection from the WebSocket group when disconnected."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages (not required in this case)."""
        pass

    async def send_notification(self, event):
        """Send notification data to the connected WebSocket clients."""
        message = event["message"]
        created_at = event["created_at"]

        await self.send(text_data=json.dumps({
            "message": message,
            "created_at": created_at,
        }))