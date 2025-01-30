from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.db.models.signals import pre_save
from django.dispatch import receiver
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