from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "oauth_provider",
    ]
    list_filter = [
        "is_staff",
        "is_superuser",
        "is_active",
        "oauth_provider",
        "date_joined",
    ]
    search_fields = ["username", "email", "first_name", "last_name"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("avatar", "oauth_provider", "oauth_uid")}),
    )
