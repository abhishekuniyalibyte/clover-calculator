from rest_framework import serializers
from .models import (
    Merchant, Competitor, Analysis,
    MerchantHardware, PricingModel, DeviceCatalogItem,
    ProposedDevice, SaaSCatalogItem, ProposedSaaS, OneTimeFee
)
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
            'monthly_volume', 'monthly_transaction_count',
            'interchange_total', 'interac_txn_count',
            'visa_volume', 'mc_volume', 'amex_volume',
            'notes', 'created_at', 'updated_at'
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
            'monthly_volume', 'monthly_transaction_count',
            'interchange_total', 'interac_txn_count',
            'visa_volume', 'mc_volume', 'amex_volume',
            'notes'
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
            if value.created_by != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
                raise serializers.ValidationError("You can only link your own statements.")
        return value

    def create(self, validated_data):
        """Automatically set user from request context"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


# ========== Merchant Hardware Serializers ==========

class MerchantHardwareSerializer(serializers.ModelSerializer):
    """Serializer for Merchant Hardware costs"""

    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    cost_type_display = serializers.CharField(source='get_cost_type_display', read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = MerchantHardware
        fields = [
            'id', 'analysis', 'item_type', 'item_type_display', 'item_name',
            'provider', 'cost_type', 'cost_type_display', 'amount', 'quantity',
            'total_cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_analysis(self, value):
        """Ensure user can only add hardware to their own analyses"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only add hardware to your own analyses.")
        return value

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value


# ========== Pricing Model Serializers ==========

class PricingModelSerializer(serializers.ModelSerializer):
    """Serializer for Pricing Models"""

    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)

    class Meta:
        model = PricingModel
        fields = [
            'id', 'analysis', 'model_type', 'model_type_display', 'is_selected',
            'markup_percent', 'card_brand_fee_percent', 'basis_points',
            'visa_rate', 'mc_rate', 'amex_rate',
            'discount_rate', 'billback_rate', 'nonqualified_pct',
            'per_transaction_fee', 'monthly_fee',
            'surcharge_rate', 'program_discount_rate',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_analysis(self, value):
        """Ensure user can only add pricing models to their own analyses"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only add pricing models to your own analyses.")
        return value

    def validate(self, data):
        """Ensure only one pricing model is selected per analysis"""
        if data.get('is_selected', False):
            analysis = data.get('analysis')
            # Check if another model is already selected for this analysis
            existing_selected = PricingModel.objects.filter(
                analysis=analysis,
                is_selected=True
            )
            # Exclude current instance if updating
            if self.instance:
                existing_selected = existing_selected.exclude(id=self.instance.id)

            if existing_selected.exists():
                raise serializers.ValidationError(
                    "Another pricing model is already selected for this analysis. "
                    "Please deselect it first."
                )
        return data


# ========== Device Catalog Serializers ==========

class DeviceCatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for Device Catalog Items"""

    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = DeviceCatalogItem
        fields = [
            'id', 'name', 'category', 'category_display', 'device_type',
            'description', 'image', 'lease_price_min', 'lease_price_max',
            'purchase_price_min', 'purchase_price_max', 'is_active',
            'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ========== Proposed Device Serializers ==========

class ProposedDeviceSerializer(serializers.ModelSerializer):
    """Serializer for Proposed Devices with nested device info"""

    device_details = DeviceCatalogItemSerializer(source='device', read_only=True)
    pricing_type_display = serializers.CharField(source='get_pricing_type_display', read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProposedDevice
        fields = [
            'id', 'analysis', 'device', 'device_details', 'quantity',
            'pricing_type', 'pricing_type_display', 'selected_price',
            'total_cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProposedDeviceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Proposed Devices"""

    class Meta:
        model = ProposedDevice
        fields = [
            'analysis', 'device', 'quantity', 'pricing_type',
            'selected_price', 'notes'
        ]

    def validate_analysis(self, value):
        """Ensure user can only add devices to their own analyses"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only add devices to your own analyses.")
        return value

    def validate_device(self, value):
        """Ensure device is active"""
        if not value.is_active:
            raise serializers.ValidationError("This device is not available for selection.")
        return value

    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_selected_price(self, value):
        """Ensure price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate(self, data):
        """Validate price is within device price range"""
        device = data.get('device')
        pricing_type = data.get('pricing_type')
        selected_price = data.get('selected_price')

        if pricing_type == 'LEASE':
            if device.lease_price_min and selected_price < device.lease_price_min:
                raise serializers.ValidationError(
                    f"Lease price must be at least ${device.lease_price_min}"
                )
            if device.lease_price_max and selected_price > device.lease_price_max:
                raise serializers.ValidationError(
                    f"Lease price cannot exceed ${device.lease_price_max}"
                )
        elif pricing_type == 'PURCHASE':
            if device.purchase_price_min and selected_price < device.purchase_price_min:
                raise serializers.ValidationError(
                    f"Purchase price must be at least ${device.purchase_price_min}"
                )
            if device.purchase_price_max and selected_price > device.purchase_price_max:
                raise serializers.ValidationError(
                    f"Purchase price cannot exceed ${device.purchase_price_max}"
                )

        return data


# ========== SaaS Catalog Serializers ==========

class SaaSCatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for SaaS Catalog Items"""

    class Meta:
        model = SaaSCatalogItem
        fields = [
            'id', 'plan_name', 'description', 'monthly_price', 'features',
            'is_active', 'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ========== Proposed SaaS Serializers ==========

class ProposedSaaSSerializer(serializers.ModelSerializer):
    """Serializer for Proposed SaaS with nested plan info"""

    saas_plan_details = SaaSCatalogItemSerializer(source='saas_plan', read_only=True)

    class Meta:
        model = ProposedSaaS
        fields = [
            'id', 'analysis', 'saas_plan', 'saas_plan_details', 'quantity',
            'monthly_cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProposedSaaSCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Proposed SaaS"""

    class Meta:
        model = ProposedSaaS
        fields = [
            'analysis', 'saas_plan', 'quantity', 'monthly_cost', 'notes'
        ]

    def validate_analysis(self, value):
        """Ensure user can only add SaaS to their own analyses"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only add SaaS plans to your own analyses.")
        return value

    def validate_saas_plan(self, value):
        """Ensure SaaS plan is active"""
        if not value.is_active:
            raise serializers.ValidationError("This SaaS plan is not available for selection.")
        return value

    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_monthly_cost(self, value):
        """Ensure monthly cost is positive"""
        if value <= 0:
            raise serializers.ValidationError("Monthly cost must be greater than 0.")
        return value


# ========== One-Time Fee Serializers ==========

class OneTimeFeeSerializer(serializers.ModelSerializer):
    """Serializer for One-Time Fees"""

    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)

    class Meta:
        model = OneTimeFee
        fields = [
            'id', 'analysis', 'fee_type', 'fee_type_display', 'fee_name',
            'amount', 'is_optional', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_analysis(self, value):
        """Ensure user can only add fees to their own analyses"""
        request = self.context.get('request')
        if value.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            raise serializers.ValidationError("You can only add fees to your own analyses.")
        return value

    def validate_amount(self, value):
        """Ensure amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value
