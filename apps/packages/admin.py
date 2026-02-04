from django.contrib import admin

from .models import Experience, HotelTier, Package, TransportOption


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ["name", "base_price", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["created_at", "base_price"]
    ordering = ["name"]


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
