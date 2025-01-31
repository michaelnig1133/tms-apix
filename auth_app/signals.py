from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.db.models.signals import pre_save,post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import User

@receiver(pre_save, sender=User)
def revoke_tokens_on_deactivation(sender, instance, **kwargs):
    if instance.id:
        try:
            old_instance = User.objects.get(id=instance.id)
            if not old_instance.is_deleted and instance.is_deleted:
                tokens = OutstandingToken.objects.filter(user=instance)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)  # Blacklist tokens instead of deleting
        except User.DoesNotExist:
            pass  


@receiver(post_save, sender=User)
def send_admin_notification(sender, instance, created, **kwargs):
    """Send real-time notifications to System Admin when a user registers or resubmits."""
    if instance.is_pending:
        message = (
            f"New registration request from {instance.full_name}"
            if created
            else f"Resubmission request received for {instance.full_name}"
        )

        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "admin_notifications",
            {
                "type": "send_notification",
                "message": message,
                "created_at": str(instance.updated_at),
            }
        )
