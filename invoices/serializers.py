from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "customer",
            "customer_email",   
            "plan",
            "plan_name",     
            "original_amount",
            "discount",  
            "amount",
            "status",
            "created_at",
            "due_date",
            "paid_at",
            "notes",
        ]
        read_only_fields = [
            "invoice_number",
            "original_amount",
            "amount",
            "created_at",
            "customer_email",
            "plan_name",
        ]