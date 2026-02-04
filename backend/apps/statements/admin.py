from django.contrib import admin
from .models import MerchantStatement, StatementData


@admin.register(MerchantStatement)
class MerchantStatementAdmin(admin.ModelAdmin):
    """Admin interface for Merchant Statement"""

    list_display = [
        'id', 'merchant_name', 'source', 'status',
        'created_by', 'created_at', 'file_name'
    ]
    list_filter = ['source', 'status', 'created_at']
    search_fields = ['merchant_name', 'file_name', 'processor_name']
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'file_size', 'file_type']

    fieldsets = (
        ('Basic Information', {
            'fields': ('created_by', 'source', 'status')
        }),
        ('File Information', {
            'fields': ('file', 'file_name', 'file_size', 'file_type')
        }),
        ('Statement Details', {
            'fields': (
                'merchant_name', 'processor_name',
                'statement_period_start', 'statement_period_end'
            )
        }),
        ('Extraction Info', {
            'fields': (
                'extraction_confidence', 'requires_review',
                'extraction_notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
    )


@admin.register(StatementData)
class StatementDataAdmin(admin.ModelAdmin):
    """Admin interface for Statement Data"""

    list_display = [
        'id', 'statement', 'total_volume',
        'transaction_count', 'created_at'
    ]
    search_fields = ['statement__merchant_name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Statement Reference', {
            'fields': ('statement',)
        }),
        ('Transaction Volumes', {
            'fields': ('total_volume', 'transaction_count')
        }),
        ('Card Breakdown', {
            'fields': (
                ('visa_volume', 'visa_count'),
                ('mastercard_volume', 'mastercard_count'),
                ('amex_volume', 'amex_count'),
                ('discover_volume', 'discover_count'),
            )
        }),
        ('Fees', {
            'fields': (
                'interchange_fees', 'assessment_fees',
                'processing_fees', 'monthly_fees', 'other_fees'
            )
        }),
        ('Rates', {
            'fields': ('effective_rate',)
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
