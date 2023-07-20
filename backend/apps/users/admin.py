from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

User = get_user_model()
ADDITIONAL_USER_FIELDS = (
    ('Блокировка пользователя', {'fields': ('block',)}),
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for User model."""
    list_filter = ('email', 'username')
    add_fieldsets = BaseUserAdmin.add_fieldsets + ADDITIONAL_USER_FIELDS
    fieldsets = BaseUserAdmin.fieldsets + ADDITIONAL_USER_FIELDS


admin.site.unregister(Group)
