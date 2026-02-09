from django.contrib import admin
from .models import Merchant, Competitor, Analysis


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    """Admin interface for Merchant model"""

    list_display = ['id', 'business_name', 'contact_name', 'user', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['business_name', 'contact_name', 'contact_email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Business Information', {
            'fields': ('user', 'business_name', 'business_address')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    """Admin interface for Competitor model"""

    list_display = ['id', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Competitor Information', {
            'fields': ('name', 'logo', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    """Admin interface for Analysis model"""

    list_display = ['id', 'merchant', 'user', 'status', 'competitor', 'created_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['merchant__business_name', 'user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['merchant', 'competitor', 'statement']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('user', 'merchant', 'statement', 'competitor', 'status')
        }),
        ('Current Costs', {
            'fields': (
                'current_processing_rate',
                'current_monthly_fees',
                'current_transaction_fees',
                'monthly_volume',
                'monthly_transaction_count'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
