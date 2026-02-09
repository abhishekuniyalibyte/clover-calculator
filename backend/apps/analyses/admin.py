from django.contrib import admin
from .models import (
    Merchant, Competitor, Analysis,
    MerchantHardware, PricingModel, DeviceCatalogItem,
    ProposedDevice, SaaSCatalogItem, ProposedSaaS, OneTimeFee
)


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


@admin.register(MerchantHardware)
class MerchantHardwareAdmin(admin.ModelAdmin):
    """Admin interface for Merchant Hardware model"""

    list_display = ['id', 'analysis', 'item_name', 'item_type', 'cost_type', 'amount', 'quantity', 'created_at']
    list_filter = ['item_type', 'cost_type', 'created_at']
    search_fields = ['item_name', 'provider', 'analysis__merchant__business_name']
    readonly_fields = ['created_at', 'updated_at', 'total_cost']
    autocomplete_fields = ['analysis']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis',)
        }),
        ('Hardware Details', {
            'fields': ('item_type', 'item_name', 'provider')
        }),
        ('Cost Information', {
            'fields': ('cost_type', 'amount', 'quantity', 'total_cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PricingModel)
class PricingModelAdmin(admin.ModelAdmin):
    """Admin interface for Pricing Model"""

    list_display = ['id', 'analysis', 'model_type', 'is_selected', 'markup_percent', 'discount_rate', 'created_at']
    list_filter = ['model_type', 'is_selected', 'created_at']
    search_fields = ['analysis__merchant__business_name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['analysis']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis', 'model_type', 'is_selected')
        }),
        ('Pricing Details', {
            'fields': ('markup_percent', 'basis_points', 'discount_rate', 'per_transaction_fee', 'monthly_fee')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceCatalogItem)
class DeviceCatalogItemAdmin(admin.ModelAdmin):
    """Admin interface for Device Catalog"""

    list_display = ['id', 'name', 'category', 'device_type', 'lease_price_min', 'purchase_price_min', 'is_active', 'sort_order']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'device_type', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Device Information', {
            'fields': ('name', 'category', 'device_type', 'description', 'image')
        }),
        ('Pricing', {
            'fields': (
                ('lease_price_min', 'lease_price_max'),
                ('purchase_price_min', 'purchase_price_max')
            )
        }),
        ('Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProposedDevice)
class ProposedDeviceAdmin(admin.ModelAdmin):
    """Admin interface for Proposed Device"""

    list_display = ['id', 'analysis', 'device', 'quantity', 'pricing_type', 'selected_price', 'created_at']
    list_filter = ['pricing_type', 'created_at']
    search_fields = ['analysis__merchant__business_name', 'device__name']
    readonly_fields = ['created_at', 'updated_at', 'total_cost']
    autocomplete_fields = ['analysis', 'device']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis',)
        }),
        ('Device Selection', {
            'fields': ('device', 'quantity', 'pricing_type', 'selected_price', 'total_cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SaaSCatalogItem)
class SaaSCatalogItemAdmin(admin.ModelAdmin):
    """Admin interface for SaaS Catalog"""

    list_display = ['id', 'plan_name', 'monthly_price', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['plan_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Plan Information', {
            'fields': ('plan_name', 'description', 'monthly_price', 'features')
        }),
        ('Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProposedSaaS)
class ProposedSaaSAdmin(admin.ModelAdmin):
    """Admin interface for Proposed SaaS"""

    list_display = ['id', 'analysis', 'saas_plan', 'quantity', 'monthly_cost', 'created_at']
    list_filter = ['created_at']
    search_fields = ['analysis__merchant__business_name', 'saas_plan__plan_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['analysis', 'saas_plan']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis',)
        }),
        ('SaaS Selection', {
            'fields': ('saas_plan', 'quantity', 'monthly_cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OneTimeFee)
class OneTimeFeeAdmin(admin.ModelAdmin):
    """Admin interface for One-Time Fee"""

    list_display = ['id', 'analysis', 'fee_type', 'fee_name', 'amount', 'is_optional', 'created_at']
    list_filter = ['fee_type', 'is_optional', 'created_at']
    search_fields = ['fee_name', 'analysis__merchant__business_name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['analysis']
    fieldsets = (
        ('Analysis Information', {
            'fields': ('analysis',)
        }),
        ('Fee Details', {
            'fields': ('fee_type', 'fee_name', 'amount', 'is_optional')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
