from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('auth_app', '0009_notification'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='user',
            new_name='recipient',
        ),
        migrations.AddField(
            model_name='notification',
            name='action_required',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('new_request', 'New Transport Request'), ('forwarded', 'Request Forwarded'), ('approved', 'Request Approved'), ('rejected', 'Request Rejected'), ('assigned', 'Vehicle Assigned')], default='new_request', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], default='normal', max_length=10),
        ),
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notification',
            name='transport_request',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.transportrequest'),
        ),
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', '-created_at'], name='auth_app_no_recipien_e8701d_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['is_read'], name='auth_app_no_is_read_b0c2ac_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['notification_type'], name='auth_app_no_notific_429156_idx'),
        ),
    ]
