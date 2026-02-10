from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Merchant, Competitor, Analysis,
    MerchantHardware, PricingModel, DeviceCatalogItem,
    ProposedDevice, SaaSCatalogItem, ProposedSaaS, OneTimeFee
)
from .calculators import AnalysisCalculator


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

    list_display = ['id', 'merchant', 'user', 'status', 'competitor', 'monthly_savings_display', 'created_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['merchant__business_name', 'user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'cost_comparison_summary']
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
                'monthly_transaction_count',
            )
        }),
        ('Extended Statement Data', {
            'fields': (
                'interchange_total',
                'interac_txn_count',
                ('visa_volume', 'mc_volume', 'amex_volume'),
            ),
            'description': 'Required for Cost Plus / iPlus (interchange_total) and Discount Rate (brand volumes).',
            'classes': ('collapse',),
        }),
        ('Cost Comparison Summary', {
            'fields': ('cost_comparison_summary',),
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def monthly_savings_display(self, obj):
        """Show monthly savings in the list view with colour coding"""
        try:
            report = AnalysisCalculator(obj).get_full_report()
            savings = report['savings']['monthly']
            color = 'green' if savings > 0 else 'red'
            return mark_safe(
                f'<span style="color:{color}; font-weight:bold;">${savings:,.2f}/mo</span>'
            )
        except Exception:
            return '—'
    monthly_savings_display.short_description = 'Monthly Savings'

    def cost_comparison_summary(self, obj):
        """Render a full cost comparison table inside the Analysis detail page"""
        try:
            report = AnalysisCalculator(obj).get_full_report()
            c = report['current_costs']
            p = report['proposed_costs']
            s = report['savings']
            o = report['onetime_costs']
            competitor = obj.competitor.name if obj.competitor else 'Current Processor'

            missing_html = ''
            if not report['has_sufficient_data']:
                missing = ', '.join(report['missing_fields'])
                missing_html = f'<p style="color:orange; font-weight:bold;">⚠ Missing data: {missing}</p>'

            break_even = f"{s['break_even_months']:.1f} months" if s['break_even_months'] else '—'

            td = "padding:8px; border:1px solid #4a90d9; color:#222;"
            td_r = "padding:8px; text-align:right; border:1px solid #4a90d9; color:#222;"

            html = f"""
                {missing_html}
                <table style="width:100%; border-collapse:collapse; font-size:14px;">
                  <thead>
                    <tr style="background:#1565c0; color:white;">
                      <th style="padding:8px; text-align:left; border:1px solid #4a90d9; color:white;">Item</th>
                      <th style="padding:8px; text-align:right; border:1px solid #4a90d9; color:white;">Current ({competitor})</th>
                      <th style="padding:8px; text-align:right; border:1px solid #4a90d9; color:white;">Proposed (Blockpay)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style="background:#fff3cd;">
                      <td style="{td}">Interchange (pass-through)</td>
                      <td style="{td_r}">included in rate</td>
                      <td style="{td_r}">${p['interchange_passthrough']:,.2f}</td>
                    </tr>
                    <tr style="background:#e8f0fe;">
                      <td style="{td}">Processing Fees (markup + brand)</td>
                      <td style="{td_r}">${c['processing_cost']:,.2f}</td>
                      <td style="{td_r}">${p['processing_cost']:,.2f}</td>
                    </tr>
                    <tr style="background:#d2e3fc;">
                      <td style="{td}">Per-Transaction Fees</td>
                      <td style="{td_r}">${c['per_transaction_cost']:,.2f}</td>
                      <td style="{td_r}">included</td>
                    </tr>
                    <tr style="background:#e8f0fe;">
                      <td style="{td}">Monthly Fees</td>
                      <td style="{td_r}">${c['monthly_fees']:,.2f}</td>
                      <td style="{td_r}">included</td>
                    </tr>
                    <tr style="background:#d2e3fc;">
                      <td style="{td}">Hardware (monthly)</td>
                      <td style="{td_r}">${c['hardware_monthly']:,.2f}</td>
                      <td style="{td_r}">${p['device_monthly']:,.2f}</td>
                    </tr>
                    <tr style="background:#e8f0fe;">
                      <td style="{td}">SaaS / Software</td>
                      <td style="{td_r}">—</td>
                      <td style="{td_r}">${p['saas_monthly']:,.2f}</td>
                    </tr>
                    <tr style="background:#1b5e20; font-weight:bold;">
                      <td style="padding:8px; border:1px solid #4a90d9; color:white; font-weight:bold;">TOTAL / MONTH</td>
                      <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:white; font-weight:bold;">${c['total_monthly']:,.2f}</td>
                      <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:white; font-weight:bold;">${p['total_monthly']:,.2f}</td>
                    </tr>
                  </tbody>
                </table>

                <table style="width:100%; border-collapse:collapse; font-size:14px; margin-top:16px;">
                  <thead>
                    <tr style="background:#1a73e8; color:white;">
                      <th style="padding:8px; text-align:left; border:1px solid #4a90d9; color:white;" colspan="2">&#128176; Savings Summary</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style="background:#e8f0fe;">
                        <td style="{td}">Daily</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold;">${s['daily']:,.2f}</td></tr>
                    <tr style="background:#d2e3fc;">
                        <td style="{td}">Weekly</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold;">${s['weekly']:,.2f}</td></tr>
                    <tr style="background:#e8f0fe;">
                        <td style="{td}">Monthly</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold;">${s['monthly']:,.2f}</td></tr>
                    <tr style="background:#d2e3fc;">
                        <td style="{td}">Quarterly</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold;">${s['quarterly']:,.2f}</td></tr>
                    <tr style="background:#e8f0fe;">
                        <td style="padding:8px; border:1px solid #4a90d9; color:#222; font-weight:bold;">Yearly</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold; font-size:16px;">${s['yearly']:,.2f}</td></tr>
                    <tr style="background:#d2e3fc;">
                        <td style="{td}">Savings %</td>
                        <td style="padding:8px; text-align:right; border:1px solid #4a90d9; color:#2e7d32; font-weight:bold;">{s['percent']:.1f}%</td></tr>
                    <tr style="background:#e8f0fe;">
                        <td style="{td}">One-Time Costs</td>
                        <td style="{td_r}">${o['total']:,.2f}</td></tr>
                    <tr style="background:#d2e3fc;">
                        <td style="{td}">Break-Even</td>
                        <td style="{td_r}">{break_even}</td></tr>
                  </tbody>
                </table>
            """
            return mark_safe(html)
        except Exception as e:
            return format_html('<p style="color:red;">Could not compute: {}</p>', str(e))

    cost_comparison_summary.short_description = 'Cost Comparison'


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
        ('Cost Plus / iPlus', {
            'fields': ('markup_percent', 'card_brand_fee_percent', 'basis_points'),
            'description': 'Cost Plus: set both markup_percent (0.10%) and card_brand_fee_percent (0.15%). iPlus: set only markup_percent (0.25%).',
        }),
        ('Discount Rate (Billback)', {
            'fields': (
                ('visa_rate', 'mc_rate', 'amex_rate'),
                'discount_rate',
                'billback_rate',
                'nonqualified_pct',
            ),
            'description': 'Set per-brand rates. billback_rate applies to nonqualified_pct% of volume.',
            'classes': ('collapse',),
        }),
        ('Surcharge Program', {
            'fields': ('surcharge_rate', 'program_discount_rate'),
            'description': 'surcharge_rate = charged to cardholder. program_discount_rate = billed to merchant on total ticket.',
            'classes': ('collapse',),
        }),
        ('Shared / Fixed Fees', {
            'fields': ('per_transaction_fee', 'monthly_fee'),
            'description': 'per_transaction_fee = Interac debit fee (default $0.04). monthly_fee = fixed account/PCI fee.',
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
