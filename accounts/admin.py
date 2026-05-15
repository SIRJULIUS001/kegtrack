from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Role, Permission


# =========================
# ROLE ADMIN
# =========================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "business", "created_at")
    list_filter = ("name", "business")
    search_fields = ("name",)


# =========================
# PERMISSION ADMIN
# =========================
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")
    search_fields = ("code", "name")


# =========================
# USER ADMIN (SAAS-READY)
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "id",
        "username",
        "email",
        "phone",
        "business",
        "role",
        "is_superadmin",
        "is_staff",
        "is_active",
        "is_deleted",
    )

    list_filter = (
        "is_superadmin",
        "is_staff",
        "is_active",
        "is_deleted",
        "role",
        "business",
    )

    search_fields = ("username", "email", "phone")

    ordering = ("-id",)

    fieldsets = (
        ("Account Info", {
            "fields": ("username", "password")
        }),

        ("Personal Info", {
            "fields": ("first_name", "last_name", "email", "phone")
        }),

        ("Business Context", {
            "fields": ("business", "role")
        }),

        ("Permissions (System)", {
            "fields": ("is_superadmin", "is_superuser", "is_staff", "is_active_staff", "is_active", "is_deleted")
        }),

        ("Security & Device", {
            "fields": ("last_login_ip", "last_device", "must_change_password")
        }),

        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        ("Create User", {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "phone",
                "password1",
                "password2",
                "business",
                "role",
                "is_superadmin",
                "is_staff",
                "is_active",
            ),
        }),
    )