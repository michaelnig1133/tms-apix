# Generated by Django 5.1.6 on 2025-04-17 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_highcosttransportrequest_trip_completed_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerequest",
            name="maintenance_letter",
            field=models.FileField(
                blank=True, null=True, upload_to="maintenance_letters/"
            ),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="maintenance_total_cost",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="receipt_file",
            field=models.FileField(
                blank=True, null=True, upload_to="maintenance_receipts/"
            ),
        ),
    ]
