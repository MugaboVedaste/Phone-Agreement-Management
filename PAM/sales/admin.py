from django.contrib import admin
from django.utils.html import format_html
from .models import SalesTransaction, SellerPerformance, SalesTarget, Customer


@admin.register(SalesTransaction)
class SalesTransactionAdmin(admin.ModelAdmin):
    """Admin interface for SalesTransaction model"""
    list_display = ['transaction_id', 'seller', 'phone_display', 'customer_name', 
                   'sale_price', 'profit', 'status', 'sale_date']
    list_filter = ['status', 'payment_method', 'sale_date', 'seller']
    search_fields = ['transaction_id', 'customer_name', 'customer_phone', 
                    'phone__imei', 'seller__username']
    readonly_fields = ['transaction_id', 'profit', 'commission_amount', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'seller', 'phone', 'agreement', 'status')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Financial Details', {
            'fields': ('sale_price', 'cost_price', 'profit', 'commission_rate', 'commission_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('Additional Information', {
            'fields': ('sale_date', 'notes'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def phone_display(self, obj):
        """Display phone details"""
        return f"{obj.phone.brand} {obj.phone.model}"
    phone_display.short_description = 'Phone'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('seller', 'phone', 'agreement')


@admin.register(SellerPerformance)
class SellerPerformanceAdmin(admin.ModelAdmin):
    """Admin interface for SellerPerformance model"""
    list_display = ['seller', 'period_type', 'period_range', 'total_sales', 
                   'total_revenue', 'total_profit', 'average_profit_margin']
    list_filter = ['period_type', 'period_start']
    search_fields = ['seller__username', 'seller__first_name', 'seller__last_name']
    readonly_fields = ['calculated_at']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('seller', 'period_type', 'period_start', 'period_end')
        }),
        ('Sales Metrics', {
            'fields': ('total_sales', 'total_revenue', 'total_cost', 'total_profit', 'total_commission')
        }),
        ('Performance Indicators', {
            'fields': ('average_sale_price', 'average_profit_margin', 'rank_in_period')
        }),
        ('System', {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def period_range(self, obj):
        """Display period range"""
        return f"{obj.period_start} to {obj.period_end}"
    period_range.short_description = 'Period'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('seller')


@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    """Admin interface for SalesTarget model"""
    list_display = ['seller', 'target_type', 'target_value', 'achieved_value', 
                   'achievement_display', 'is_active', 'is_achieved']
    list_filter = ['target_type', 'is_active', 'is_achieved', 'start_date']
    search_fields = ['seller__username', 'notes']
    readonly_fields = ['achievement_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Target Information', {
            'fields': ('seller', 'target_type', 'target_value', 'achieved_value')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_achieved', 'achievement_date')
        }),
        ('Incentive', {
            'fields': ('incentive_amount', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['update_progress', 'activate_targets', 'deactivate_targets']
    
    def achievement_display(self, obj):
        """Display achievement percentage with color coding"""
        percentage = obj.get_achievement_percentage()
        if percentage >= 100:
            color = 'green'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    achievement_display.short_description = 'Achievement'
    
    def update_progress(self, request, queryset):
        """Action to update progress of selected targets"""
        for target in queryset:
            target.update_progress()
        self.message_user(request, f'{queryset.count()} targets updated.')
    update_progress.short_description = 'Update progress of selected targets'
    
    def activate_targets(self, request, queryset):
        """Action to activate selected targets"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} targets activated.')
    activate_targets.short_description = 'Activate selected targets'
    
    def deactivate_targets(self, request, queryset):
        """Action to deactivate selected targets"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} targets deactivated.')
    deactivate_targets.short_description = 'Deactivate selected targets'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('seller')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model"""
    list_display = ['name', 'phone', 'total_purchases', 'total_spent', 
                   'average_purchase_value', 'last_purchase_date', 'is_active']
    list_filter = ['is_active', 'first_purchase_date', 'registered_by']
    search_fields = ['name', 'phone', 'email', 'national_id']
    readonly_fields = ['total_purchases', 'total_spent', 'average_purchase_value',
                      'first_purchase_date', 'last_purchase_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'phone', 'email', 'national_id', 'address')
        }),
        ('Purchase Metrics', {
            'fields': ('total_purchases', 'total_spent', 'average_purchase_value',
                      'first_purchase_date', 'last_purchase_date')
        }),
        ('Registration', {
            'fields': ('registered_by', 'is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['update_customer_metrics']
    
    def update_customer_metrics(self, request, queryset):
        """Action to update metrics for selected customers"""
        for customer in queryset:
            customer.update_metrics()
        self.message_user(request, f'{queryset.count()} customer metrics updated.')
    update_customer_metrics.short_description = 'Update metrics for selected customers'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('registered_by')
