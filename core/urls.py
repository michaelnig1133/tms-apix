from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import (
    TransportRequestActionView, 
    TransportRequestCreateView, 
    TransportRequestListView,
    NotificationListView, 
    NotificationMarkReadView, 
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
)



urlpatterns = [
   path('',TransportRequestCreateView.as_view(),name="create-transport-request"),
   path('list/',TransportRequestListView.as_view(),name="list-transport-request"),
   path('<int:request_id>/action/',TransportRequestActionView.as_view(),name="transport-request-action"),
   path('transport-requests/', TransportRequestListView.as_view(), name='transport-request-list'),
   path('transport-requests/create/', TransportRequestCreateView.as_view(), name='transport-request-create'),
   path('transport-requests/<int:request_id>/action/', TransportRequestActionView.as_view(), name='transport-request-action'),
   # Notification endpoints
   path('notifications/', NotificationListView.as_view(), name='notifications'),
   path('notifications/<int:notification_id>/read/', NotificationMarkReadView.as_view(), name='mark-notification-read'),
   path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='mark-all-notifications-read'),
   path('notifications/unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),
]

