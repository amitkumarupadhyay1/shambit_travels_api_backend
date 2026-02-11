from decimal import Decimal

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import path
from django.utils.html import format_html

from .admin_views import ExperienceAnalyticsDashboard
from .models import Experience, HotelTier, Package, TransportOption


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "city",
        "base_price",
        "duration_hours",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "category",
        "difficulty_level",
        "city",
        "created_at",
    ]
    search_fields = ["name", "description"]
    list_editable = ["is_active", "base_price"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 25

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "description", "category", "city")},
        ),
        (
            "Details",
            {"fields": ("duration_hours", "max_participants", "difficulty_level")},
        ),
        (
            "Pricing & Media",
            {"fields": ("base_price", "featured_image")},
        ),
        (
            "Status",
            {"fields": ("is_active", "created_at", "updated_at")},
        ),
    )

    def get_urls(self):
        """Add custom URL for analytics dashboard"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "analytics/",
                self.admin_site.admin_view(ExperienceAnalyticsDashboard.as_view()),
                name="packages_experience_analytics",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add analytics link to changelist view"""
        extra_context = extra_context or {}
        extra_context["analytics_url"] = "analytics/"
        return super().changelist_view(request, extra_context)

    # Existing actions
    @admin.action(description="Activate selected experiences")
    def activate_experiences(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} experience(s) successfully activated.", level="success"
        )

    @admin.action(description="Deactivate selected experiences")
    def deactivate_experiences(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} experience(s) successfully deactivated.",
            level="success",
        )

    @admin.action(description="Duplicate selected experiences")
    def duplicate_experience(self, request, queryset):
        count = 0
        for exp in queryset:
            exp.pk = None
            exp.name = f"{exp.name} (Copy)"
            exp.save()
            count += 1
        self.message_user(
            request, f"{count} experience(s) successfully duplicated.", level="success"
        )

    # New bulk operations
    @admin.action(description="Increase prices by 10%")
    def bulk_price_increase(self, request: HttpRequest, queryset: QuerySet):
        """Increase prices by 10%"""
        count = 0
        for exp in queryset:
            exp.base_price = exp.base_price * Decimal("1.10")
            exp.save()
            count += 1
        self.message_user(
            request,
            f"Increased prices by 10% for {count} experience(s).",
            level="success",
        )

    @admin.action(description="Decrease prices by 10%")
    def bulk_price_decrease(self, request: HttpRequest, queryset: QuerySet):
        """Decrease prices by 10%"""
        count = 0
        for exp in queryset:
            new_price = exp.base_price * Decimal("0.90")
            # Ensure price doesn't go below minimum
            if new_price >= 100:
                exp.base_price = new_price
                exp.save()
                count += 1
        self.message_user(
            request,
            f"Decreased prices by 10% for {count} experience(s). "
            f"Skipped experiences that would go below ₹100.",
            level="success",
        )

    @admin.action(description="Change category to CULTURAL")
    def bulk_change_category(self, request: HttpRequest, queryset: QuerySet):
        """Change category to CULTURAL (example - can be extended with form)"""
        updated = queryset.update(category="CULTURAL")
        self.message_user(
            request,
            f"Changed category to CULTURAL for {updated} experience(s). "
            f"Note: For other categories, use individual edit.",
            level="warning",
        )

    @admin.action(description="Activate all in same city")
    def bulk_activate_by_city(self, request: HttpRequest, queryset: QuerySet):
        """Activate all experiences in the same cities as selected"""
        cities = queryset.values_list("city", flat=True).distinct()
        updated = Experience.objects.filter(city__in=cities).update(is_active=True)
        self.message_user(
            request,
            f"Activated {updated} experience(s) in selected cities.",
            level="success",
        )

    @admin.action(description="Deactivate all in same city")
    def bulk_deactivate_by_city(self, request: HttpRequest, queryset: QuerySet):
        """Deactivate all experiences in the same cities as selected"""
        cities = queryset.values_list("city", flat=True).distinct()
        updated = Experience.objects.filter(city__in=cities).update(is_active=False)
        self.message_user(
            request,
            f"Deactivated {updated} experience(s) in selected cities.",
            level="warning",
        )


@admin.register(HotelTier)
class HotelTierAdmin(admin.ModelAdmin):
    list_display = ["name", "price_multiplier"]
    search_fields = ["name", "description"]
    list_filter = ["price_multiplier"]
    ordering = ["price_multiplier"]


@admin.register(TransportOption)
class TransportOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "base_price"]
    search_fields = ["name", "description"]
    list_filter = ["base_price"]
    ordering = ["base_price"]


class PackageExperienceInline(admin.TabularInline):
    model = Package.experiences.through
    extra = 1


class PackageHotelTierInline(admin.TabularInline):
    model = Package.hotel_tiers.through
    extra = 1


class PackageTransportInline(admin.TabularInline):
    model = Package.transport_options.through
    extra = 1


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "is_active", "created_at"]
    list_filter = ["is_active", "city", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active"]

    inlines = [PackageExperienceInline, PackageHotelTierInline, PackageTransportInline]

    fieldsets = (
        (
            "Basic Info",
            {"fields": ("name", "slug", "city", "description", "is_active")},
        ),
    )

    def get_queryset(self, request):
        # Optimize admin queryset with select_related and prefetch_related
        return (
            super()
            .get_queryset(request)
            .select_related("city")
            .prefetch_related("experiences", "hotel_tiers", "transport_options")
        )
