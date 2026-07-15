# invoices/views.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Invoice
from .serializers import InvoiceSerializer
from .permissions import IsAdminOrReadOnlyForOwner
from rest_framework.decorators import action
from django.db.models import Sum
 

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnlyForOwner]

    def get_queryset(self):
        user = self.request.user
        # Admin sees all invoices
        if getattr(user, "role", None) == "admin":
            return Invoice.objects.all().order_by("-created_at")
        # Normal user sees only their own invoices
        return Invoice.objects.filter(customer=user).order_by("-created_at")

    def perform_create(self, serializer):
        """
        Only admin can create invoices. Amount auto-filled from plan price.
        """
        user = self.request.user
        if getattr(user, "role", None) != "admin":
            raise PermissionError("Only admin can create invoices")
        serializer.save()  # invoice_number & amount handled in model save()

    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        """
        Update only invoice status
        URL: /invoices/{id}/update-status/
        """
        user = request.user

        # Only admin allowed
        if getattr(user, "role", None) != "admin":
            return Response(
                {"error": "Only admin can update status"},
                status=status.HTTP_403_FORBIDDEN,
            )

        invoice = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Invoice.STATUS_CHOICES):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = new_status

        # Auto set paid_at if paid
        if new_status == "paid":
            from django.utils import timezone

            invoice.paid_at = timezone.now()

        invoice.save()

        return Response(
            {
                "success": True,
                "message": "Status updated successfully",
                "data": InvoiceSerializer(invoice).data,
            }
        )



    @action(detail=False, methods=["get"], url_path="total-revenue")
    def total_revenue(self, request):
        """
        Returns:
        - total revenue (paid invoices only)
        - paid invoice count
        - pending invoice count
        """

        user = request.user

        # Base queryset
        if getattr(user, "role", None) == "admin":
            qs = Invoice.objects.all()
        else:
            qs = Invoice.objects.filter(customer=user)

        paid_qs = qs.filter(status="paid")
        pending_qs = qs.filter(status="pending")

        total_revenue = paid_qs.aggregate(total=Sum("amount"))["total"] or 0

        return Response(
            {
                "success": True,
                "total_revenue": float(total_revenue),
                "paid_invoices_count": paid_qs.count(),
                "pending_invoices_count": pending_qs.count(),
            }
        )
