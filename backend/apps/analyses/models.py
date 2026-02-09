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
        help_text='Number of transactions per month'
    )

    # Analysis notes
    notes = models.TextField(
        blank=True,
        help_text='Agent notes and observations'
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
