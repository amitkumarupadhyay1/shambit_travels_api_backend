from django.contrib import admin

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "city", "author", "status", "created_at"]
    list_filter = ["status", "city", "created_at"]
    search_fields = ["title", "content", "author"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Content",
            {"fields": ("title", "slug", "city", "content", "author", "status")},
        ),
        (
            "SEO",
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        # Optimize admin queryset with select_related
        return super().get_queryset(request).select_related("city")
