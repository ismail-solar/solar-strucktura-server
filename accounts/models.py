# accounts/models.py/

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


class Customer(AbstractUser):
    username = None
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
        ('demo', 'Demo'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    address = models.CharField(max_length=255, blank=True, null=True)
    plain_password = models.CharField(max_length=255, blank=True, null=True)
    is_active_account = models.BooleanField(default=True) 
    is_demo_active = models.BooleanField(default=False)
    demo_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'   # login using email
    REQUIRED_FIELDS = []       # no extra required fields
    
    def is_demo_expired(self):
        if self.role != "demo":
            return False
        if self.demo_expires_at and self.demo_expires_at < now():
            return True
        return False

    def __str__(self):
        return f"{self.email} ({self.role})"




class UserSession(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)  # 👈 ADD THIS
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    







