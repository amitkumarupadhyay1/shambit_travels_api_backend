from django.contrib import admin

from .models import Traveler


@admin.register(Traveler)
class TravelerAdmin(admin.ModelAdmin):
    list_display = ["name", "age", "age_group", "gender", "user", "updated_at"]
    list_filter = ["gender", "created_at", "updated_at"]
    search_fields = ["name", "email", "phone", "user__email"]
    readonly_fields = ["created_at", "updated_at", "age_group"]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "name", "age", "gender")}),
        ("Contact Information", {"fields": ("email", "phone")}),
        (
            "Travel Documents",
            {"fields": ("nationality", "passport_number", "date_of_birth")},
        ),
        (
            "Metadata",
            {
                "fields": ("age_group", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")
