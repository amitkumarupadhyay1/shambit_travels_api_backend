from django.contrib import admin

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

    actions = ["activate_experiences", "deactivate_experiences", "duplicate_experience"]

    def activate_experiences(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} experience(s) successfully activated.", level="success"
        )

    activate_experiences.short_description = "Activate selected experiences"

    def deactivate_experiences(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} experience(s) successfully deactivated.",
            level="success",
        )

    deactivate_experiences.short_description = "Deactivate selected experiences"

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

    duplicate_experience.short_description = "Duplicate selected experiences"


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
