from rest_framework import serializers
from .models import Merchant, Competitor, Analysis
from apps.statements.models import MerchantStatement


class MerchantSerializer(serializers.ModelSerializer):
    """Serializer for Merchant model"""

    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Merchant
        fields = [
            'id', 'user', 'user_name', 'business_name', 'business_address',
            'contact_name', 'contact_email', 'contact_phone', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Automatically set user from request context"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class CompetitorSerializer(serializers.ModelSerializer):
    """Serializer for Competitor model"""

    class Meta:
        model = Competitor
        fields = [
            'id', 'name', 'logo', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AnalysisListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing analyses"""

    user_name = serializers.CharField(source='user.username', read_only=True)
    merchant_name = serializers.CharField(source='merchant.business_name', read_only=True)
    competitor_name = serializers.CharField(source='competitor.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Analysis
        fields = [
            'id', 'user', 'user_name', 'merchant', 'merchant_name',
            'competitor', 'competitor_name', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']


class AnalysisDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Analysis model"""

    user_name = serializers.CharField(source='user.username', read_only=True)
    merchant_details = MerchantSerializer(source='merchant', read_only=True)
    competitor_details = CompetitorSerializer(source='competitor', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Analysis
        fields = [
            'id', 'user', 'user_name', 'merchant', 'merchant_details',
            'statement', 'competitor', 'competitor_details', 'status', 'status_display',
            'current_processing_rate', 'current_monthly_fees', 'current_transaction_fees',
            'monthly_volume', 'monthly_transaction_count', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Automatically set user from request context"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class AnalysisCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating analyses"""

    class Meta:
        model = Analysis
        fields = [
            'merchant', 'statement', 'competitor', 'status',
            'current_processing_rate', 'current_monthly_fees', 'current_transaction_fees',
            'monthly_volume', 'monthly_transaction_count', 'notes'
        ]

    def validate_merchant(self, value):
        """Ensure user can only link their own merchants"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only create analyses for your own merchants.")
        return value

    def validate_statement(self, value):
        """Ensure user can only link their own statements"""
        if value:
            request = self.context.get('request')
            if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
                raise serializers.ValidationError("You can only link your own statements.")
        return value

    def create(self, validated_data):
        """Automatically set user from request context"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
