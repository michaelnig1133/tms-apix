from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.timezone import now
from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    EMPLOYEE = 1
    DEPARTMENT_MANAGER = 2
    FINANCE_MANAGER = 3
    TRANSPORT_MANAGER = 4
    CEO = 5
    DRIVER = 6
    SYSTEM_ADMIN = 7

    ROLE_CHOICES = (
        (EMPLOYEE, 'Employee'),
        (DEPARTMENT_MANAGER, 'Department Manager'),
        (FINANCE_MANAGER, 'Finance Manager'),
        (TRANSPORT_MANAGER, 'Transport Manager'),
        (CEO, 'CEO'),
        (DRIVER, 'Driver'),
        (SYSTEM_ADMIN, 'System Admin'),
    )

    id = models.AutoField(primary_key=True, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES,default=1)
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)  
    is_pending = models.BooleanField(default=True)  
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
  