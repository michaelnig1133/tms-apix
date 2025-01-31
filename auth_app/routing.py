from django.urls import re_path
from .consumers import AdminNotificationConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", AdminNotificationConsumer.as_asgi()),
]
