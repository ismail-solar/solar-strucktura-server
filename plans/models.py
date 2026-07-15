# plans/models.py/

from django.db import models
from accounts.models import Customer
from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):
    TOOL_CHOICES = [
        ("t1", "BOM + 2D Drawing"),
        ("t2", "Layout Designer"),
        ("hybrid", "Hybrid (T1 + T2)"),
    ]

    name = models.CharField(max_length=50)
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES)
    features = models.TextField(
        blank=True, help_text="Enter features separated by commas"
    )

    # Separate limits for T1 and T2
    t1_projects_limit = models.IntegerField(
        null=True, blank=True, help_text="Leave empty if not applicable"
    )
    t2_projects_limit = models.IntegerField(
        null=True, blank=True, help_text="Leave empty if not applicable"
    )
    is_unlimited = models.BooleanField(default=False)
    duration_days = models.IntegerField(default=30)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Invoice price for this plan",
    )

    def __str__(self):
        return f"{self.name} ({self.get_tool_display()})"
    class Meta:
        ordering = ["tool", "price"]


class UserPlan(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=False)
    t1_projects_used = models.IntegerField(default=0)
    t2_projects_used = models.IntegerField(default=0)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.customer.name} - {self.plan.name if self.plan else 'No Plan'}"
