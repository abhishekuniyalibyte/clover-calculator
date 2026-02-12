from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from apps.statements.models import MerchantStatement

User = get_user_model()


class Merchant(models.Model):
    """Model for merchant business information"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='merchants',
        help_text='Agent who created this merchant'
    )
    business_name = models.CharField(
        max_length=255,
        help_text='DBA (Doing Business As) name'
    )
    business_address = models.TextField(
        help_text='Full business address'
    )
    contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Primary contact person name'
    )
    contact_email = models.EmailField(
        validators=[EmailValidator()],
        blank=True,
        help_text='Primary contact email'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Primary contact phone number'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the merchant'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_merchant'
        verbose_name = 'Merchant'
        verbose_name_plural = 'Merchants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['business_name']),
        ]

    def __str__(self):
        return f"{self.business_name} (ID: {self.id})"


class Competitor(models.Model):
    """Model for payment processor competitors"""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Competitor/Processor name (e.g., Chase, Square, Stripe)'
    )
    logo = models.ImageField(
        upload_to='competitors/logos/',
        null=True,
        blank=True,
        help_text='Competitor logo image'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the competitor'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this competitor is actively used'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_competitor'
        verbose_name = 'Competitor'
        verbose_name_plural = 'Competitors'
        ordering = ['name']

    def __str__(self):
        return self.name


class Analysis(models.Model):
    """Model for merchant cost analysis"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_REVIEW', 'In Review'),
        ('COMPLETED', 'Completed'),
        ('SUBMITTED', 'Submitted'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analyses',
        help_text='Agent who created this analysis'
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name='analyses',
        help_text='Merchant being analyzed'
    )
    statement = models.ForeignKey(
        MerchantStatement,
        on_delete=models.SET_NULL,
        related_name='analyses',
        null=True,
        blank=True,
        help_text='Associated merchant statement (if uploaded)'
    )
    competitor = models.ForeignKey(
        Competitor,
        on_delete=models.SET_NULL,
        related_name='analyses',
        null=True,
        blank=True,
        help_text='Current payment processor/competitor'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        help_text='Current status of the analysis'
    )

    # Current costs (manually entered or extracted from statement)
    current_processing_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current processing rate percentage (e.g., 2.50 for 2.5%)'
    )
    current_monthly_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current monthly fees in dollars'
    )
    current_transaction_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Current per-transaction fees in dollars'
    )
    monthly_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monthly transaction volume in dollars'
    )
    monthly_transaction_count = models.IntegerField(
        null=True,
        blank=True,
        help_text='Total number of credit transactions per month'
    )

    # Extended statement data — for model-specific accurate calculations
    interchange_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monthly interchange (pass-through) total in dollars — from statement (used in Cost Plus / iPlus proposals)'
    )
    interac_txn_count = models.IntegerField(
        null=True,
        blank=True,
        help_text='Number of Interac debit transactions per month ($0.04/txn in Blockpay proposals)'
    )
    visa_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monthly Visa credit volume in dollars (for Discount Rate per-brand calculation)'
    )
    mc_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monthly Mastercard credit volume in dollars (for Discount Rate per-brand calculation)'
    )
    amex_volume = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Monthly Amex volume in dollars (for Discount Rate per-brand calculation)'
    )

    # Analysis notes
    notes = models.TextField(
        blank=True,
        help_text='Agent notes and observations'
    )

    # Generated proposal PDF
    generated_pdf = models.FileField(
        upload_to='proposals/',
        null=True,
        blank=True,
        help_text='Generated Blockpay proposal PDF'
    )
    generated_pdf_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the proposal PDF was last generated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_analysis'
        verbose_name = 'Analysis'
        verbose_name_plural = 'Analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['merchant', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Analysis for {self.merchant.business_name} ({self.get_status_display()})"

    @property
    def is_draft(self):
        """Check if analysis is in draft status"""
        return self.status == 'DRAFT'

    @property
    def is_completed(self):
        """Check if analysis is completed"""
        return self.status == 'COMPLETED'

    @property
    def is_submitted(self):
        """Check if analysis is submitted"""
        return self.status == 'SUBMITTED'


class MerchantHardware(models.Model):
    """Model for merchant's current hardware/software costs"""

    ITEM_TYPE_CHOICES = [
        ('POS_TERMINAL', 'POS Terminal'),
        ('CARD_READER', 'Card Reader'),
        ('PRINTER', 'Printer'),
        ('SCANNER', 'Scanner'),
        ('SOFTWARE', 'Software'),
        ('OTHER', 'Other'),
    ]

    COST_TYPE_CHOICES = [
        ('MONTHLY_LEASE', 'Monthly Lease'),
        ('MONTHLY_SUBSCRIPTION', 'Monthly Subscription'),
        ('ONE_TIME_PURCHASE', 'One-Time Purchase'),
        ('PER_TRANSACTION', 'Per Transaction'),
    ]

    analysis = models.ForeignKey(
        'Analysis',
        on_delete=models.CASCADE,
        related_name='hardware_costs',
        help_text='Analysis this hardware cost belongs to'
    )
    item_type = models.CharField(
        max_length=30,
        choices=ITEM_TYPE_CHOICES,
        help_text='Type of hardware/software item'
    )
    item_name = models.CharField(
        max_length=255,
        help_text='Name of the hardware/software (e.g., "Square Terminal")'
    )
    provider = models.CharField(
        max_length=100,
        blank=True,
        help_text='Provider/vendor name (e.g., "Square", "Clover")'
    )
    cost_type = models.CharField(
        max_length=30,
        choices=COST_TYPE_CHOICES,
        help_text='Type of cost structure'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Cost amount in dollars'
    )
    quantity = models.IntegerField(
        default=1,
        help_text='Number of units'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this hardware/software'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_merchanthardware'
        verbose_name = 'Merchant Hardware'
        verbose_name_plural = 'Merchant Hardware'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', '-created_at']),
            models.Index(fields=['item_type']),
        ]

    def __str__(self):
        return f"{self.item_name} - {self.get_item_type_display()} (Analysis: {self.analysis.id})"

    @property
    def total_cost(self):
        """Calculate total cost based on quantity"""
        return self.amount * self.quantity


class PricingModel(models.Model):
    """Model for Blockpay pricing proposals"""

    MODEL_TYPE_CHOICES = [
        ('COST_PLUS', 'Cost-Plus (Interchange+)'),
        ('I_PLUS', 'iPlus'),
        ('DISCOUNT_RATE', 'Discount Rate (Billback)'),
        ('SURCHARGE', 'Surcharge Program'),
    ]

    analysis = models.ForeignKey(
        'Analysis',
        on_delete=models.CASCADE,
        related_name='pricing_models',
        help_text='Analysis this pricing model belongs to'
    )
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        help_text='Type of pricing model'
    )
    is_selected = models.BooleanField(
        default=False,
        help_text='Whether this is the selected pricing model for the proposal'
    )
    # --- Cost Plus / iPlus fields ---
    markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Blockpay markup % on credit volume. Cost Plus default: 0.10%; iPlus default: 0.25%'
    )
    card_brand_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Card brand fee % on credit volume (Cost Plus only). Default: 0.15%. Do NOT use for iPlus.'
    )
    basis_points = models.IntegerField(
        null=True,
        blank=True,
        help_text='Markup in basis points (informational; 10 bps = 0.10%)'
    )

    # --- Discount Rate (Billback) fields ---
    visa_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Visa base discount rate %. Blockpay default: 1.36%'
    )
    mc_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Mastercard base discount rate %. Blockpay default: 1.38%'
    )
    amex_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Amex base discount rate %. Blockpay default: 2.65%'
    )
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Fallback discount rate % if per-brand rates (visa_rate/mc_rate/amex_rate) are not set'
    )
    billback_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Non-qualified/billback surcharge % on non-qualifying transactions. Default: 0.25%'
    )
    nonqualified_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Estimated % of monthly volume that is non-qualified (keyed, CNP, premium). e.g., 15 for 15%'
    )

    # --- Shared per-item and fixed fields ---
    per_transaction_fee = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Interac debit per-transaction fee in dollars. Blockpay default: $0.04'
    )
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Fixed monthly fee in dollars (account fee, PCI program, etc.)'
    )

    # --- Surcharge Program fields ---
    surcharge_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Surcharge % charged to cardholder on eligible credit transactions (e.g., 2.40)'
    )
    program_discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text='Program discount % billed to merchant on total ticket (sale + surcharge). e.g., 2.343'
    )

    notes = models.TextField(
        blank=True,
        help_text='Additional notes, assumptions used, or override justification'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_pricingmodel'
        verbose_name = 'Pricing Model'
        verbose_name_plural = 'Pricing Models'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', 'is_selected']),
            models.Index(fields=['model_type']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['analysis', 'model_type'],
                name='unique_analysis_model_type'
            )
        ]

    def __str__(self):
        return f"{self.get_model_type_display()} for Analysis {self.analysis.id}"


class DeviceCatalogItem(models.Model):
    """Admin-managed catalog of Clover devices"""

    CATEGORY_CHOICES = [
        ('DEVICE', 'Device'),
        ('ACCESSORY', 'Accessory'),
        ('GATEWAY', 'Gateway'),
    ]

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Device name (e.g., "Clover Flex", "Clover Mini")'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text='Device category'
    )
    device_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Device type/model (e.g., "Flex", "Mini", "Station Duo")'
    )
    description = models.TextField(
        blank=True,
        help_text='Device description and features'
    )
    image = models.ImageField(
        upload_to='devices/',
        null=True,
        blank=True,
        help_text='Device image'
    )
    lease_price_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum monthly lease price'
    )
    lease_price_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum monthly lease price'
    )
    purchase_price_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum one-time purchase price'
    )
    purchase_price_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum one-time purchase price'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this device is available for selection'
    )
    sort_order = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_devicecatalogitem'
        verbose_name = 'Device Catalog Item'
        verbose_name_plural = 'Device Catalog Items'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class ProposedDevice(models.Model):
    """Devices proposed for a specific analysis"""

    PRICING_TYPE_CHOICES = [
        ('LEASE', 'Lease'),
        ('PURCHASE', 'Purchase'),
    ]

    analysis = models.ForeignKey(
        'Analysis',
        on_delete=models.CASCADE,
        related_name='proposed_devices',
        help_text='Analysis this device proposal belongs to'
    )
    device = models.ForeignKey(
        DeviceCatalogItem,
        on_delete=models.PROTECT,
        related_name='proposals',
        help_text='Device from the catalog'
    )
    quantity = models.IntegerField(
        default=1,
        help_text='Number of devices'
    )
    pricing_type = models.CharField(
        max_length=10,
        choices=PRICING_TYPE_CHOICES,
        help_text='Lease or purchase'
    )
    selected_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Selected price (monthly for lease, one-time for purchase)'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this device proposal'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_proposeddevice'
        verbose_name = 'Proposed Device'
        verbose_name_plural = 'Proposed Devices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', '-created_at']),
        ]

    def __str__(self):
        return f"{self.device.name} x{self.quantity} ({self.get_pricing_type_display()}) - Analysis {self.analysis.id}"

    @property
    def total_cost(self):
        """Calculate total cost based on quantity"""
        return self.selected_price * self.quantity


class SaaSCatalogItem(models.Model):
    """Admin-managed catalog of Clover SaaS plans"""

    plan_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='SaaS plan name (e.g., "Clover Essentials", "Clover Register")'
    )
    description = models.TextField(
        blank=True,
        help_text='Plan description and features'
    )
    monthly_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Monthly subscription price'
    )
    features = models.JSONField(
        default=dict,
        blank=True,
        help_text='Plan features as JSON (e.g., {"max_devices": 5, "inventory": true})'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this plan is available for selection'
    )
    sort_order = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_saascatalogitem'
        verbose_name = 'SaaS Catalog Item'
        verbose_name_plural = 'SaaS Catalog Items'
        ordering = ['sort_order', 'plan_name']

    def __str__(self):
        return f"{self.plan_name} (${self.monthly_price}/month)"


class ProposedSaaS(models.Model):
    """SaaS plans proposed for a specific analysis"""

    analysis = models.ForeignKey(
        'Analysis',
        on_delete=models.CASCADE,
        related_name='proposed_saas',
        help_text='Analysis this SaaS proposal belongs to'
    )
    saas_plan = models.ForeignKey(
        SaaSCatalogItem,
        on_delete=models.PROTECT,
        related_name='proposals',
        help_text='SaaS plan from the catalog'
    )
    quantity = models.IntegerField(
        default=1,
        help_text='Number of subscriptions/additional devices'
    )
    monthly_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total monthly cost for this SaaS item'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this SaaS proposal'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_proposedsaas'
        verbose_name = 'Proposed SaaS'
        verbose_name_plural = 'Proposed SaaS'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', '-created_at']),
        ]

    def __str__(self):
        return f"{self.saas_plan.plan_name} x{self.quantity} - Analysis {self.analysis.id}"


class OneTimeFee(models.Model):
    """One-time fees for a specific analysis"""

    FEE_TYPE_CHOICES = [
        ('APPLICATION', 'Application Fee'),
        ('DEPLOYMENT', 'Deployment Fee'),
        ('SHIPPING', 'Shipping Fee'),
        ('INSURANCE', 'Insurance Fee'),
        ('SETUP', 'Setup Fee'),
        ('OTHER', 'Other Fee'),
    ]

    analysis = models.ForeignKey(
        'Analysis',
        on_delete=models.CASCADE,
        related_name='onetime_fees',
        help_text='Analysis this fee belongs to'
    )
    fee_type = models.CharField(
        max_length=20,
        choices=FEE_TYPE_CHOICES,
        help_text='Type of one-time fee'
    )
    fee_name = models.CharField(
        max_length=255,
        help_text='Name/description of the fee'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Fee amount in dollars'
    )
    is_optional = models.BooleanField(
        default=False,
        help_text='Whether this fee is optional'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about this fee'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analyses_onetimefee'
        verbose_name = 'One-Time Fee'
        verbose_name_plural = 'One-Time Fees'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', 'fee_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.fee_name} (${self.amount}) - Analysis {self.analysis.id}"
