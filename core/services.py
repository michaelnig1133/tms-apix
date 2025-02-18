from django.utils.translation import gettext as _
from auth_app.models import User
from core.models import TransportRequest, Notification


class NotificationService:
    NOTIFICATION_TEMPLATES = {
        'new_request': {
            'title': _("New Transport Request"),
            'message': _("{requester} has submitted a new transport request to {destination} on {date}"),
            'priority': 'normal'
        },
        'forwarded': {
            'title': _("Transport Request Forwarded"),
            'message': _("Transport request #{request_id} has been forwarded for your approval"),
            'priority': 'normal'
        },
        'approved': {
            'title': _("Transport Request Approved"),
            'message': _("Your transport request #{request_id} has been approved by {approver}"),
            'priority': 'normal'
        },
        'rejected': {
            'title': _("Transport Request Rejected"),
            'message': _("Your transport request #{request_id} has been rejected by {rejector}"),
            'priority': 'high'
        },
        'assigned': {
            'title': _("Vehicle Assigned"),
            'message': _("Vehicle and driver have been assigned to request #{request_id}"),
            'priority': 'normal'
        }
    }

    @classmethod
    def create_notification(cls, notification_type: str, transport_request: TransportRequest, 
                          recipient: User, **kwargs) -> Notification:
        """
        Create a new notification
        """
        template = cls.NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            raise ValueError(f"Invalid notification type: {notification_type}")

        # Format message with provided kwargs
        message_kwargs = {
            'request_id': transport_request.id,
            'requester': transport_request.requester.full_name,
            'destination': transport_request.destination,
            'date': transport_request.start_day.strftime('%Y-%m-%d'),
            **kwargs
        }

        notification = Notification.objects.create(
            recipient=recipient,
            transport_request=transport_request,
            notification_type=notification_type,
            title=template['title'],
            message=template['message'].format(**message_kwargs),
            priority=template['priority'],
            action_required=notification_type not in ['approved', 'rejected'],
            metadata={
                'request_id': transport_request.id,
                'requester_id': transport_request.requester.id,
                'destination': transport_request.destination,
                'date': transport_request.start_day.strftime('%Y-%m-%d'),
                **kwargs
            }
        )
        return notification

    @classmethod
    def mark_as_read(cls, notification_id: int) -> None:
        """
        Mark a notification as read
        """
        Notification.objects.filter(id=notification_id).update(is_read=True)

    @classmethod
    def get_user_notifications(cls, user_id: int, unread_only: bool = False, 
                             page: int = 1, page_size: int = 20):
        """
        Get notifications for a user with pagination
        """
        queryset = Notification.objects.filter(recipient_id=user_id)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        start = (page - 1) * page_size
        end = start + page_size
        return queryset[start:end]

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """
        Get count of unread notifications for a user
        """
        return Notification.objects.filter(recipient_id=user_id, is_read=False).count()

    @classmethod
    def clean_old_notifications(cls, days: int = 90) -> int:
        """
        Clean notifications older than specified days
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return Notification.objects.filter(created_at__lt=cutoff_date).delete()[0]
