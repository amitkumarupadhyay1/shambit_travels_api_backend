from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["razorpay_order_id", "booking", "amount", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["razorpay_order_id", "razorpay_payment_id", "booking__user__email"]
    readonly_fields = [
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Payment Info", {"fields": ("booking", "amount", "status")}),
        (
            "Razorpay Details",
            {
                "fields": (
                    "razorpay_order_id",
                    "razorpay_payment_id",
                    "razorpay_signature",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        # Optimize admin queryset with select_related
        return (
            super()
            .get_queryset(request)
            .select_related("booking__user", "booking__package__city")
        )
