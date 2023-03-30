from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, Genre, Title, User


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "description")
    search_fields = ("name",)


@admin.register(User)
class MyUserAdmin(UserAdmin):

    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "bio",
    ]
    list_editable = ("role",)
    fieldsets = (
        (
            None,
            {"fields": ("username", "email", "role", "bio")},
        ),
        (
            "Permissions",
            {"fields": ("is_active",)},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "is_active",
                    "bio",
                    "role",
                ),
            },
        ),
    )
    ordering = ("email",)
    search_fields = ("username", "role")
    list_filter = (
        "role",
        "is_active",
    )
    empty_value_display = "-пусто-"
