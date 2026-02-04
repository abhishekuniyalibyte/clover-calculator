from rest_framework import serializers
from .models import MerchantStatement, StatementData


class StatementDataSerializer(serializers.ModelSerializer):
    """Serializer for statement data"""

    class Meta:
        model = StatementData
        fields = [
            'total_volume', 'transaction_count',
            'visa_volume', 'visa_count',
            'mastercard_volume', 'mastercard_count',
            'amex_volume', 'amex_count',
            'discover_volume', 'discover_count',
            'interchange_fees', 'assessment_fees',
            'processing_fees', 'monthly_fees', 'other_fees',
            'effective_rate'
        ]


class MerchantStatementSerializer(serializers.ModelSerializer):
    """Serializer for merchant statement"""

    data = StatementDataSerializer(read_only=True)

    class Meta:
        model = MerchantStatement
        fields = [
            'id', 'source', 'status', 'file_name', 'file_size',
            'merchant_name', 'processor_name',
            'statement_period_start', 'statement_period_end',
            'extraction_confidence', 'requires_review',
            'created_at', 'processed_at', 'data'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload"""

    file = serializers.FileField(required=True)

    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")

        # Check file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Invalid file type. Only PDF and images are allowed."
            )

        return value


class ManualEntrySerializer(serializers.Serializer):
    """Serializer for manual data entry"""

    merchant_name = serializers.CharField(required=True, max_length=255)
    business_type = serializers.CharField(required=False, allow_blank=True, max_length=100)
    period_start = serializers.DateField(required=True)
    period_end = serializers.DateField(required=True)

    total_volume = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    transaction_count = serializers.IntegerField(required=True, min_value=1)

    interchange_fees = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fees = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_fees = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_fees = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)

    def validate(self, attrs):
        """Validate dates"""
        if attrs['period_start'] > attrs['period_end']:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date'
            })
        return attrs
