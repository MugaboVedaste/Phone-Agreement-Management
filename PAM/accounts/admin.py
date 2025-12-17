from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin for CustomUser model.
    Extends Django's UserAdmin with additional fields.
    """
    list_display = ['username', 'email', 'role', 'is_suspended', 'phone_number', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_suspended', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'phone_number', 'national_id', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('role', 'phone_number', 'address', 'national_id', 'signature')
        }),
        ('Suspension Status', {
            'fields': ('is_suspended', 'suspended_at', 'suspended_reason', 'suspended_by')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Information', {
            'fields': ('role', 'phone_number', 'address', 'national_id')
        }),
    )
    
    readonly_fields = ['suspended_at', 'date_joined']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('suspended_by')
