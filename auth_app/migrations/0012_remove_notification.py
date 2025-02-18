from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0011_update_notification'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Notification',
        ),
    ]
