from django.db import models
from django.conf import settings


class MerchantStatement(models.Model):
    """Uploaded merchant statement document"""

    SOURCE_CHOICES = [
        ('UPLOAD', 'PDF/Image Upload'),
        ('MANUAL', 'Manual Entry'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Processing'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statements'
    )

    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # File information (for uploads)
    file = models.FileField(upload_to='statements/%Y/%m/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True)

    # Statement metadata
    merchant_name = models.CharField(max_length=255, blank=True)
    processor_name = models.CharField(max_length=100, blank=True)
    statement_period_start = models.DateField(null=True, blank=True)
    statement_period_end = models.DateField(null=True, blank=True)

    # Extraction status
    extraction_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    requires_review = models.BooleanField(default=False)
    extraction_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'statements_merchantstatement'
        verbose_name = 'Merchant Statement'
        verbose_name_plural = 'Merchant Statements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Statement {self.id} - {self.merchant_name or 'Unknown'} ({self.get_source_display()})"


class StatementData(models.Model):
    """Extracted or manually entered statement data"""

    statement = models.OneToOneField(
        MerchantStatement,
        on_delete=models.CASCADE,
        related_name='data'
    )

    # Transaction volumes
    total_volume = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = models.IntegerField()

    # Card type breakdowns
    visa_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    visa_count = models.IntegerField(default=0)
    mastercard_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mastercard_count = models.IntegerField(default=0)
    amex_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amex_count = models.IntegerField(default=0)
    discover_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discover_count = models.IntegerField(default=0)
    interac_volume = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    interac_count = models.IntegerField(default=0)

    # Fees from current processor
    interchange_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    assessment_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Rate information
    effective_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True
    )

    # Raw extracted data (for review)
    raw_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'statements_statementdata'
        verbose_name = 'Statement Data'
        verbose_name_plural = 'Statement Data'

    def __str__(self):
        return f"Data for Statement {self.statement.id}"
