# invoices/models.py
from django.db import models
from django.utils import timezone
from accounts.models import Customer
from plans.models import Plan
import uuid

class Invoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # stores original plan price
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # fixed discount
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    # FINAL AMOUNT (after discount)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    
    
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-SLR-{uuid.uuid4().hex[:8].upper()}"
        # STEP 1: Get base price from plan
        base_amount = self.plan.price if self.plan else 0

        # STEP 2: Store original amount (important)
        self.original_amount = base_amount

        # STEP 3: Apply FIXED discount
        discount_value = self.discount if self.discount else 0
        final_amount = base_amount - discount_value
        # STEP 4: Prevent negative values
        self.amount = max(final_amount, 0)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number