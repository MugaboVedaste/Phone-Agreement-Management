from django.contrib import admin
from .models import Phone, Agreement, PhoneHistory, PhoneAssignment


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    """Admin interface for Phone model"""
    list_display = ['imei', 'brand', 'model', 'color', 'condition', 'status', 'current_owner', 'created_at']
    list_filter = ['status', 'condition', 'brand', 'created_at']
    search_fields = ['imei', 'serial_number', 'brand', 'model', 'color']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Phone Identifiers', {
            'fields': ('imei', 'serial_number')
        }),
        ('Phone Details', {
            'fields': ('brand', 'model', 'color', 'condition')
        }),
        ('Ownership & Status', {
            'fields': ('current_owner', 'status', 'purchase_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('current_owner')


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    """Admin interface for Agreement model"""
    list_display = ['__str__', 'agreement_type', 'seller', 'customer_name', 'price', 'created_at']
    list_filter = ['agreement_type', 'created_at']
    search_fields = ['customer_name', 'customer_national_id', 'customer_phone', 'phone__imei']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Agreement Information', {
            'fields': ('agreement_type', 'phone', 'seller')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_national_id', 'customer_phone', 'customer_address')
        }),
        ('Documents', {
            'fields': ('id_photo', 'passport_photo', 'signature', 'signature_photo')
        }),
        ('Transaction', {
            'fields': ('price', 'notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('phone', 'seller')


@admin.register(PhoneHistory)
class PhoneHistoryAdmin(admin.ModelAdmin):
    """Admin interface for PhoneHistory model"""
    list_display = ['phone', 'action', 'from_user', 'to_user', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['phone__imei', 'notes', 'from_user__username', 'to_user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('History Entry', {
            'fields': ('phone', 'action')
        }),
        ('Users Involved', {
            'fields': ('from_user', 'to_user')
        }),
        ('Details', {
            'fields': ('agreement', 'notes', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('phone', 'from_user', 'to_user', 'agreement')
    
    def has_add_permission(self, request):
        """Prevent manual addition - history is auto-created"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - immutable audit trail"""
        return False


@admin.register(PhoneAssignment)
class PhoneAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for PhoneAssignment model"""
    list_display = ['phone', 'from_seller', 'to_seller', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['phone__imei', 'from_seller__username', 'to_seller__username', 'message']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('phone', 'status')
        }),
        ('Sellers', {
            'fields': ('from_seller', 'to_seller')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('phone', 'from_seller', 'to_seller')
