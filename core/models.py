from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()


class Vehicle(models.Model):
    ORGANIZATION_OWNED = 'organization'
    RENTED = 'rented'

    VEHICLE_SOURCE_CHOICES = [
        (ORGANIZATION_OWNED, 'Organization Owned'),
        (RENTED, 'Rented'),
    ]

    license_plate = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)
    capacity = models.IntegerField()
    is_available = models.BooleanField(default=True)
    source = models.CharField(max_length=20, choices=VEHICLE_SOURCE_CHOICES, default=ORGANIZATION_OWNED)
    rental_company = models.CharField(max_length=255, blank=True, null=True) 

    def clean(self):
        if self.source == self.RENTED and not self.rental_company:
            raise ValidationError({"rental_company": "Rental company is required for rented vehicles."})

    def __str__(self):
        return f"{self.model} ({self.license_plate}) - {self.get_source_display()}"


class TransportRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('forwarded', 'Forwarded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transport_requests')
    start_day = models.DateField()
    return_day = models.DateField()
    start_time = models.TimeField()
    destination = models.CharField(max_length=255)
    reason = models.TextField()
    employees = models.ManyToManyField(User, related_name='travel_group')
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)
    driver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_approver_role = models.PositiveSmallIntegerField(choices=User.ROLE_CHOICES, default=User.DEPARTMENT_MANAGER)
    rejection_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.requester.get_full_name()} - {self.destination} ({self.status})"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_request', 'New Transport Request'),
        ('forwarded', 'Request Forwarded'),
        ('approved', 'Request Approved'),
        ('rejected', 'Request Rejected'),
        ('assigned', 'Vehicle Assigned'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    )

    recipient = models.ForeignKey('auth_app.User', on_delete=models.CASCADE, related_name='notifications')
    transport_request = models.ForeignKey(TransportRequest, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_required = models.BooleanField(default=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.full_name}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
