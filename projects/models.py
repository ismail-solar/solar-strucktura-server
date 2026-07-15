# Create your models here.
from django.db import models
from accounts.models import Customer


class Project(models.Model):
    TOOL_CHOICES = (
        ("t1", "BOM & 2D Drawing"),
        ("t2", "Layout Designer"),
    )
    user = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="projects"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    capacity = models.CharField(max_length=100, null=True, blank=True) 
    project_type = models.CharField(
        max_length=10, choices=TOOL_CHOICES, null=True, blank=True
    )
    is_draft = models.BooleanField(default=False) 
    # Only input data (your payload)
    data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.email}"
