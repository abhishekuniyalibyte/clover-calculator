from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .calculators import AnalysisCalculator

from .models import (
    Merchant, Competitor, Analysis,
    MerchantHardware, PricingModel, DeviceCatalogItem,
    ProposedDevice, SaaSCatalogItem, ProposedSaaS, OneTimeFee
)
from .serializers import (
    MerchantSerializer,
    CompetitorSerializer,
    AnalysisListSerializer,
    AnalysisDetailSerializer,
    AnalysisCreateUpdateSerializer,
    MerchantHardwareSerializer,
    PricingModelSerializer,
    DeviceCatalogItemSerializer,
    ProposedDeviceSerializer,
    ProposedDeviceCreateUpdateSerializer,
    SaaSCatalogItemSerializer,
    ProposedSaaSSerializer,
    ProposedSaaSCreateUpdateSerializer,
    OneTimeFeeSerializer
)
from apps.accounts.permissions import IsAdmin, IsOwnerOrAdmin, IsAdminOrReadOnly


# ===== Merchant Views =====

class MerchantListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating merchants
    GET /api/v1/analyses/merchants/ - List all user's merchants
    POST /api/v1/analyses/merchants/ - Create new merchant
    """
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['business_name', 'contact_name', 'contact_email']
    ordering_fields = ['business_name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return merchants for current user (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Merchant.objects.all()
        return Merchant.objects.filter(user=user)


class MerchantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a merchant
    GET /api/v1/analyses/merchants/{id}/ - Get merchant details
    PUT /api/v1/analyses/merchants/{id}/ - Update merchant
    DELETE /api/v1/analyses/merchants/{id}/ - Delete merchant
    """
    serializer_class = MerchantSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return merchants for current user (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Merchant.objects.all()
        return Merchant.objects.filter(user=user)


# ===== Competitor Views =====

class CompetitorListView(generics.ListAPIView):
    """
    API endpoint for listing competitors (read-only for agents)
    GET /api/v1/analyses/competitors/ - List all active competitors
    """
    queryset = Competitor.objects.filter(is_active=True)
    serializer_class = CompetitorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class CompetitorCreateView(generics.CreateAPIView):
    """
    API endpoint for creating competitors (admin only)
    POST /api/v1/analyses/competitors/create/ - Create new competitor
    """
    queryset = Competitor.objects.all()
    serializer_class = CompetitorSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class CompetitorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for managing competitors (admin only for write)
    GET /api/v1/analyses/competitors/{id}/ - Get competitor details
    PUT /api/v1/analyses/competitors/{id}/ - Update competitor (admin only)
    DELETE /api/v1/analyses/competitors/{id}/ - Delete competitor (admin only)
    """
    queryset = Competitor.objects.all()
    serializer_class = CompetitorSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


# ===== Analysis Views =====

class AnalysisListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating analyses
    GET /api/v1/analyses/ - List all user's analyses
    POST /api/v1/analyses/ - Create new analysis
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'merchant', 'competitor']
    search_fields = ['merchant__business_name', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return AnalysisCreateUpdateSerializer
        return AnalysisListSerializer

    def get_queryset(self):
        """Return analyses for current user (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Analysis.objects.all().select_related('user', 'merchant', 'competitor')
        return Analysis.objects.filter(user=user).select_related('user', 'merchant', 'competitor')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = serializer.save()

        # Return detailed response
        response_serializer = AnalysisDetailSerializer(analysis, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AnalysisDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting an analysis
    GET /api/v1/analyses/{id}/ - Get analysis details
    PUT /api/v1/analyses/{id}/ - Update analysis
    PATCH /api/v1/analyses/{id}/ - Partial update
    DELETE /api/v1/analyses/{id}/ - Delete analysis
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """Use different serializers for retrieve and update"""
        if self.request.method in ['PUT', 'PATCH']:
            return AnalysisCreateUpdateSerializer
        return AnalysisDetailSerializer

    def get_queryset(self):
        """Return analyses for current user (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return Analysis.objects.all().select_related('user', 'merchant', 'competitor', 'statement')
        return Analysis.objects.filter(user=user).select_related('user', 'merchant', 'competitor', 'statement')

    def update(self, request, *args, **kwargs):
        """Override update to return detailed response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return detailed response
        response_serializer = AnalysisDetailSerializer(instance, context={'request': request})
        return Response(response_serializer.data)


# ===== Merchant Hardware Views =====

class MerchantHardwareListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating merchant hardware costs
    GET /api/v1/analyses/hardware/ - List hardware costs
    POST /api/v1/analyses/hardware/ - Create new hardware cost
    """
    serializer_class = MerchantHardwareSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['analysis', 'item_type', 'cost_type']
    search_fields = ['item_name', 'provider']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return hardware for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return MerchantHardware.objects.all().select_related('analysis')
        return MerchantHardware.objects.filter(analysis__user=user).select_related('analysis')


class MerchantHardwareDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting merchant hardware
    GET /api/v1/analyses/hardware/{id}/ - Get hardware details
    PUT /api/v1/analyses/hardware/{id}/ - Update hardware
    DELETE /api/v1/analyses/hardware/{id}/ - Delete hardware
    """
    serializer_class = MerchantHardwareSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return hardware for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return MerchantHardware.objects.all().select_related('analysis')
        return MerchantHardware.objects.filter(analysis__user=user).select_related('analysis')


# ===== Pricing Model Views =====

class PricingModelListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating pricing models
    GET /api/v1/analyses/pricing-models/ - List pricing models
    POST /api/v1/analyses/pricing-models/ - Create new pricing model
    """
    serializer_class = PricingModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['analysis', 'model_type', 'is_selected']
    ordering_fields = ['created_at', 'model_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return pricing models for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return PricingModel.objects.all().select_related('analysis')
        return PricingModel.objects.filter(analysis__user=user).select_related('analysis')


class PricingModelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting pricing models
    GET /api/v1/analyses/pricing-models/{id}/ - Get pricing model details
    PUT /api/v1/analyses/pricing-models/{id}/ - Update pricing model
    DELETE /api/v1/analyses/pricing-models/{id}/ - Delete pricing model
    """
    serializer_class = PricingModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return pricing models for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return PricingModel.objects.all().select_related('analysis')
        return PricingModel.objects.filter(analysis__user=user).select_related('analysis')


# ===== Device Catalog Views =====

class DeviceCatalogListView(generics.ListAPIView):
    """
    API endpoint for listing device catalog items (read-only for agents)
    GET /api/v1/analyses/catalog/devices/ - List all active devices
    """
    queryset = DeviceCatalogItem.objects.filter(is_active=True)
    serializer_class = DeviceCatalogItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'device_type', 'description']
    ordering_fields = ['sort_order', 'name', 'lease_price_min', 'purchase_price_min']
    ordering = ['sort_order', 'name']


class DeviceCatalogCreateView(generics.CreateAPIView):
    """
    API endpoint for creating device catalog items (admin only)
    POST /api/v1/analyses/catalog/devices/create/ - Create new device
    """
    queryset = DeviceCatalogItem.objects.all()
    serializer_class = DeviceCatalogItemSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class DeviceCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for managing device catalog items (admin only for write)
    GET /api/v1/analyses/catalog/devices/{id}/ - Get device details
    PUT /api/v1/analyses/catalog/devices/{id}/ - Update device (admin only)
    DELETE /api/v1/analyses/catalog/devices/{id}/ - Delete device (admin only)
    """
    queryset = DeviceCatalogItem.objects.all()
    serializer_class = DeviceCatalogItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


# ===== Proposed Device Views =====

class ProposedDeviceListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating proposed devices
    GET /api/v1/analyses/proposed-devices/ - List proposed devices
    POST /api/v1/analyses/proposed-devices/ - Create new proposed device
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['analysis', 'device', 'pricing_type']
    ordering_fields = ['created_at', 'selected_price']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return ProposedDeviceCreateUpdateSerializer
        return ProposedDeviceSerializer

    def get_queryset(self):
        """Return proposed devices for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return ProposedDevice.objects.all().select_related('analysis', 'device')
        return ProposedDevice.objects.filter(analysis__user=user).select_related('analysis', 'device')


class ProposedDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting proposed devices
    GET /api/v1/analyses/proposed-devices/{id}/ - Get proposed device details
    PUT /api/v1/analyses/proposed-devices/{id}/ - Update proposed device
    DELETE /api/v1/analyses/proposed-devices/{id}/ - Delete proposed device
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """Use different serializers for retrieve and update"""
        if self.request.method in ['PUT', 'PATCH']:
            return ProposedDeviceCreateUpdateSerializer
        return ProposedDeviceSerializer

    def get_queryset(self):
        """Return proposed devices for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return ProposedDevice.objects.all().select_related('analysis', 'device')
        return ProposedDevice.objects.filter(analysis__user=user).select_related('analysis', 'device')


# ===== SaaS Catalog Views =====

class SaaSCatalogListView(generics.ListAPIView):
    """
    API endpoint for listing SaaS catalog items (read-only for agents)
    GET /api/v1/analyses/catalog/saas/ - List all active SaaS plans
    """
    queryset = SaaSCatalogItem.objects.filter(is_active=True)
    serializer_class = SaaSCatalogItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['plan_name', 'description']
    ordering_fields = ['sort_order', 'plan_name', 'monthly_price']
    ordering = ['sort_order', 'plan_name']


class SaaSCatalogCreateView(generics.CreateAPIView):
    """
    API endpoint for creating SaaS catalog items (admin only)
    POST /api/v1/analyses/catalog/saas/create/ - Create new SaaS plan
    """
    queryset = SaaSCatalogItem.objects.all()
    serializer_class = SaaSCatalogItemSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class SaaSCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for managing SaaS catalog items (admin only for write)
    GET /api/v1/analyses/catalog/saas/{id}/ - Get SaaS plan details
    PUT /api/v1/analyses/catalog/saas/{id}/ - Update SaaS plan (admin only)
    DELETE /api/v1/analyses/catalog/saas/{id}/ - Delete SaaS plan (admin only)
    """
    queryset = SaaSCatalogItem.objects.all()
    serializer_class = SaaSCatalogItemSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


# ===== Proposed SaaS Views =====

class ProposedSaaSListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating proposed SaaS plans
    GET /api/v1/analyses/proposed-saas/ - List proposed SaaS plans
    POST /api/v1/analyses/proposed-saas/ - Create new proposed SaaS plan
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['analysis', 'saas_plan']
    ordering_fields = ['created_at', 'monthly_cost']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for list and create"""
        if self.request.method == 'POST':
            return ProposedSaaSCreateUpdateSerializer
        return ProposedSaaSSerializer

    def get_queryset(self):
        """Return proposed SaaS for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return ProposedSaaS.objects.all().select_related('analysis', 'saas_plan')
        return ProposedSaaS.objects.filter(analysis__user=user).select_related('analysis', 'saas_plan')


class ProposedSaaSDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting proposed SaaS plans
    GET /api/v1/analyses/proposed-saas/{id}/ - Get proposed SaaS details
    PUT /api/v1/analyses/proposed-saas/{id}/ - Update proposed SaaS
    DELETE /api/v1/analyses/proposed-saas/{id}/ - Delete proposed SaaS
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """Use different serializers for retrieve and update"""
        if self.request.method in ['PUT', 'PATCH']:
            return ProposedSaaSCreateUpdateSerializer
        return ProposedSaaSSerializer

    def get_queryset(self):
        """Return proposed SaaS for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return ProposedSaaS.objects.all().select_related('analysis', 'saas_plan')
        return ProposedSaaS.objects.filter(analysis__user=user).select_related('analysis', 'saas_plan')


# ===== One-Time Fee Views =====

class OneTimeFeeListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating one-time fees
    GET /api/v1/analyses/onetime-fees/ - List one-time fees
    POST /api/v1/analyses/onetime-fees/ - Create new one-time fee
    """
    serializer_class = OneTimeFeeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['analysis', 'fee_type', 'is_optional']
    search_fields = ['fee_name']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return fees for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return OneTimeFee.objects.all().select_related('analysis')
        return OneTimeFee.objects.filter(analysis__user=user).select_related('analysis')


class OneTimeFeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting one-time fees
    GET /api/v1/analyses/onetime-fees/{id}/ - Get fee details
    PUT /api/v1/analyses/onetime-fees/{id}/ - Update fee
    DELETE /api/v1/analyses/onetime-fees/{id}/ - Delete fee
    """
    serializer_class = OneTimeFeeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Return fees for current user's analyses (or all for admins)"""
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return OneTimeFee.objects.all().select_related('analysis')
        return OneTimeFee.objects.filter(analysis__user=user).select_related('analysis')


# ===== Calculation View =====

class AnalysisCalculateView(APIView):
    """
    Compute on-the-fly cost comparison for a given analysis.
    GET /api/v1/analyses/{id}/calculate/

    Returns:
    - current_costs: what the merchant currently pays
    - proposed_costs: what they would pay under Blockpay
    - onetime_costs: one-time purchase/fee totals
    - savings: monthly, yearly, and timeframe breakdown
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = get_object_or_404(
            Analysis.objects.select_related('merchant').prefetch_related(
                'hardware_costs',
                'pricing_models',
                'proposed_devices',
                'proposed_saas',
                'onetime_fees',
            ),
            pk=pk
        )

        # Agents can only see their own analyses; admins/superusers see all
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            if analysis.user != request.user:
                raise PermissionDenied("You do not have permission to view this analysis.")

        calculator = AnalysisCalculator(analysis)
        report = calculator.get_full_report()
        return Response(report)


# ===== Phase 3: Frontend-Ready API Views =====

class AnalysisSummaryView(APIView):
    """
    Complete analysis snapshot in one shot — merchant, competitor, statement,
    hardware, pricing, devices, SaaS, fees, AND calculated cost comparison.
    GET /api/v1/analyses/{id}/summary/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = get_object_or_404(
            Analysis.objects.select_related('merchant', 'competitor', 'statement')
            .prefetch_related(
                'hardware_costs',
                'pricing_models',
                'proposed_devices__device',
                'proposed_saas__saas_plan',
                'onetime_fees',
            ),
            pk=pk
        )

        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            if analysis.user != request.user:
                raise PermissionDenied("You do not have permission to view this analysis.")

        calculator = AnalysisCalculator(analysis)
        report = calculator.get_full_report()

        response_data = {
            'analysis_id': analysis.id,
            'status': analysis.status,
            'created_at': analysis.created_at,
            'updated_at': analysis.updated_at,
            'notes': analysis.notes,
            'merchant': {
                'id': analysis.merchant.id,
                'business_name': analysis.merchant.business_name,
                'business_address': analysis.merchant.business_address,
                'contact_name': analysis.merchant.contact_name,
                'contact_email': analysis.merchant.contact_email,
                'contact_phone': analysis.merchant.contact_phone,
            },
            'competitor': {
                'id': analysis.competitor.id,
                'name': analysis.competitor.name,
                'logo_url': request.build_absolute_uri(analysis.competitor.logo.url) if analysis.competitor.logo else None,
            } if analysis.competitor else None,
            'statement': {
                'id': analysis.statement.id,
                'status': analysis.statement.status,
                'extraction_confidence': float(analysis.statement.extraction_confidence) if analysis.statement.extraction_confidence else None,
                'merchant_name': analysis.statement.merchant_name,
                'processor_name': analysis.statement.processor_name,
            } if analysis.statement else None,
            'hardware': [
                {
                    'id': hw.id,
                    'item_name': hw.item_name,
                    'item_type': hw.item_type,
                    'provider': hw.provider,
                    'cost_type': hw.cost_type,
                    'amount': float(hw.amount),
                    'quantity': hw.quantity,
                    'monthly_cost': float(hw.amount * hw.quantity) if hw.cost_type in ('MONTHLY_LEASE', 'MONTHLY_SUBSCRIPTION') else 0,
                }
                for hw in analysis.hardware_costs.all()
            ],
            'pricing_model': None,
            'proposed_devices': [
                {
                    'id': pd.id,
                    'device_name': pd.device.name,
                    'device_image_url': request.build_absolute_uri(pd.device.image.url) if pd.device.image else None,
                    'quantity': pd.quantity,
                    'pricing_type': pd.pricing_type,
                    'selected_price': float(pd.selected_price),
                    'total_cost': float(pd.total_cost),
                }
                for pd in analysis.proposed_devices.all()
            ],
            'proposed_saas': [
                {
                    'id': ps.id,
                    'plan_name': ps.saas_plan.plan_name,
                    'quantity': ps.quantity,
                    'monthly_cost': float(ps.monthly_cost),
                }
                for ps in analysis.proposed_saas.all()
            ],
            'onetime_fees': [
                {
                    'id': fee.id,
                    'fee_name': fee.fee_name,
                    'fee_type': fee.fee_type,
                    'amount': float(fee.amount),
                    'is_optional': fee.is_optional,
                }
                for fee in analysis.onetime_fees.all()
            ],
            'calculation': report,
        }

        selected_pricing = calculator.selected_pricing
        if selected_pricing:
            response_data['pricing_model'] = {
                'id': selected_pricing.id,
                'model_type': selected_pricing.model_type,
                'display_name': selected_pricing.get_model_type_display(),
                'is_selected': selected_pricing.is_selected,
                'markup_percent': float(selected_pricing.markup_percent) if selected_pricing.markup_percent else None,
                'per_transaction_fee': float(selected_pricing.per_transaction_fee) if selected_pricing.per_transaction_fee else None,
                'monthly_fee': float(selected_pricing.monthly_fee) if selected_pricing.monthly_fee else None,
            }

        return Response(response_data)


class CostBreakdownView(APIView):
    """
    Chart-ready cost breakdown data for visualizations (pie charts, bar charts).
    GET /api/v1/analyses/{id}/cost-breakdown/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = get_object_or_404(
            Analysis.objects.select_related('merchant').prefetch_related(
                'hardware_costs',
                'pricing_models',
                'proposed_devices',
                'proposed_saas',
                'onetime_fees',
            ),
            pk=pk
        )

        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            if analysis.user != request.user:
                raise PermissionDenied("You do not have permission to view this analysis.")

        calculator = AnalysisCalculator(analysis)
        current = calculator.calculate_current_costs()
        proposed = calculator.calculate_proposed_costs()
        onetime = calculator.calculate_onetime_costs()
        savings = calculator.calculate_savings(
            current['total_monthly'],
            proposed['total_monthly'],
            onetime['total'],
        )

        current_total = current['total_monthly']
        proposed_total = proposed['total_monthly']

        # Pie chart breakdown — competitor (current) costs
        competitor_breakdown = []
        for label, amount in [
            ('Processing Fees', current['processing_cost']),
            ('Per-Transaction Fees', current['per_transaction_cost']),
            ('Monthly Fees', current['monthly_fees']),
            ('Hardware / Software', current['hardware_monthly']),
        ]:
            if amount > 0:
                competitor_breakdown.append({
                    'label': label,
                    'amount': amount,
                    'percentage': round(amount / current_total * 100, 1) if current_total > 0 else 0,
                })

        # Pie chart breakdown — Blockpay (proposed) costs
        blockpay_breakdown = []
        for label, amount in [
            ('Processing Fees', proposed['processing_cost']),
            ('Device Lease', proposed['device_monthly']),
            ('SaaS Plans', proposed['saas_monthly']),
        ]:
            if amount > 0:
                blockpay_breakdown.append({
                    'label': label,
                    'amount': amount,
                    'percentage': round(amount / proposed_total * 100, 1) if proposed_total > 0 else 0,
                })

        return Response({
            'analysis_id': analysis.id,
            'competitor_costs': {
                'total': current_total,
                'breakdown': competitor_breakdown,
            },
            'blockpay_costs': {
                'total': proposed_total,
                'breakdown': blockpay_breakdown,
            },
            'one_time_costs': {
                'total': onetime['total'],
                'device_purchase': onetime['device_purchase'],
                'required_fees': onetime['required_fees'],
                'optional_fees': onetime['optional_fees'],
            },
            'savings': {
                'monthly': savings['monthly'],
                'yearly': savings['yearly'],
                'percentage': savings['percent'],
                'break_even_months': savings['break_even_months'],
            },
            'savings_timeline': [
                {'period': 'daily',     'label': 'Daily',     'amount': savings['daily']},
                {'period': 'weekly',    'label': 'Weekly',    'amount': savings['weekly']},
                {'period': 'monthly',   'label': 'Monthly',   'amount': savings['monthly']},
                {'period': 'quarterly', 'label': 'Quarterly', 'amount': savings['quarterly']},
                {'period': 'yearly',    'label': 'Yearly',    'amount': savings['yearly']},
            ],
            'bar_chart': {
                'labels': ['Processing', 'Per-Transaction', 'Monthly Fees', 'Hardware', 'Device Lease', 'SaaS'],
                'competitor': [
                    current['processing_cost'],
                    current['per_transaction_cost'],
                    current['monthly_fees'],
                    current['hardware_monthly'],
                    0,
                    0,
                ],
                'blockpay': [
                    proposed['processing_cost'],
                    0,
                    0,
                    0,
                    proposed['device_monthly'],
                    proposed['saas_monthly'],
                ],
            },
        })


class ProposalPreviewView(APIView):
    """
    Full proposal preview — all data needed for the Review Summary Screen (step 16)
    and as input for PDF generation (step 18).
    GET /api/v1/analyses/{id}/proposal-preview/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        analysis = get_object_or_404(
            Analysis.objects.select_related('merchant', 'competitor', 'statement')
            .prefetch_related(
                'hardware_costs',
                'pricing_models',
                'proposed_devices__device',
                'proposed_saas__saas_plan',
                'onetime_fees',
            ),
            pk=pk
        )

        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            if analysis.user != request.user:
                raise PermissionDenied("You do not have permission to view this analysis.")

        calculator = AnalysisCalculator(analysis)
        current = calculator.calculate_current_costs()
        proposed = calculator.calculate_proposed_costs()
        onetime = calculator.calculate_onetime_costs()
        savings = calculator.calculate_savings(
            current['total_monthly'],
            proposed['total_monthly'],
            onetime['total'],
        )
        selected_pricing = calculator.selected_pricing

        return Response({
            'analysis_id': analysis.id,
            'status': analysis.status,
            'merchant': {
                'id': analysis.merchant.id,
                'business_name': analysis.merchant.business_name,
                'business_address': analysis.merchant.business_address,
            },
            'competitor': {
                'id': analysis.competitor.id,
                'name': analysis.competitor.name,
                'logo_url': request.build_absolute_uri(analysis.competitor.logo.url) if analysis.competitor.logo else None,
                'current_monthly_cost': current['total_monthly'],
            } if analysis.competitor else None,
            'blockpay_proposal': {
                'pricing_model': {
                    'type': selected_pricing.model_type,
                    'display_name': selected_pricing.get_model_type_display(),
                    'markup_percent': float(selected_pricing.markup_percent) if selected_pricing.markup_percent else None,
                    'per_transaction_fee': float(selected_pricing.per_transaction_fee) if selected_pricing.per_transaction_fee else None,
                    'monthly_fee': float(selected_pricing.monthly_fee) if selected_pricing.monthly_fee else None,
                    'processing_cost': proposed['processing_cost'],
                } if selected_pricing else None,
                'devices': [
                    {
                        'id': pd.device.id,
                        'name': pd.device.name,
                        'category': pd.device.category,
                        'image_url': request.build_absolute_uri(pd.device.image.url) if pd.device.image else None,
                        'quantity': pd.quantity,
                        'pricing_type': pd.pricing_type,
                        'monthly_cost': float(pd.total_cost) if pd.pricing_type == 'LEASE' else 0,
                        'one_time_cost': float(pd.total_cost) if pd.pricing_type == 'PURCHASE' else 0,
                    }
                    for pd in analysis.proposed_devices.all()
                ],
                'saas_plans': [
                    {
                        'id': ps.saas_plan.id,
                        'plan_name': ps.saas_plan.plan_name,
                        'quantity': ps.quantity,
                        'monthly_cost': float(ps.monthly_cost),
                    }
                    for ps in analysis.proposed_saas.all()
                ],
                'one_time_fees': [
                    {
                        'id': fee.id,
                        'fee_name': fee.fee_name,
                        'fee_type': fee.fee_type,
                        'amount': float(fee.amount),
                        'is_optional': fee.is_optional,
                    }
                    for fee in analysis.onetime_fees.all()
                ],
                'total_monthly': proposed['total_monthly'],
                'total_one_time': onetime['total'],
            },
            'savings_summary': {
                'monthly': savings['monthly'],
                'yearly': savings['yearly'],
                'percentage': savings['percent'],
                'break_even_months': savings['break_even_months'],
                'daily': savings['daily'],
                'weekly': savings['weekly'],
                'quarterly': savings['quarterly'],
            },
        })


class AnalysisImportFromStatementView(APIView):
    """
    Auto-populate Analysis fields from the linked statement's extracted data.
    POST /api/v1/analyses/{id}/import-from-statement/

    Copies StatementData → Analysis fields:
      total_volume         → monthly_volume
      effective_rate       → current_processing_rate
      monthly_fees         → current_monthly_fees
      transaction_count    → monthly_transaction_count
      interchange_fees     → interchange_total
      interac_count        → interac_txn_count
      visa_volume          → visa_volume
      mastercard_volume    → mc_volume
      amex_volume          → amex_volume

    Only overwrites fields that have a non-zero extracted value.
    Returns the updated analysis fields so the frontend can refresh.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        analysis = get_object_or_404(Analysis, pk=pk)

        # Ownership check
        if not (request.user.is_superuser or request.user.role == 'ADMIN'):
            if analysis.user != request.user:
                raise PermissionDenied("You do not have permission to modify this analysis.")

        # Must have a linked statement
        if not analysis.statement:
            return Response(
                {'error': 'This analysis has no linked statement. Please link a statement first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Statement must be processed
        stmt = analysis.statement
        if stmt.status != 'COMPLETED':
            return Response(
                {'error': f'Statement is not yet processed (status: {stmt.status}). Please wait for processing to complete.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the extracted StatementData
        try:
            data = stmt.data
        except Exception:
            return Response(
                {'error': 'No extracted data found for this statement. Processing may have failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        imported = {}

        # Map StatementData → Analysis (only overwrite if extracted value is meaningful)
        if data.total_volume and data.total_volume > 0:
            analysis.monthly_volume = data.total_volume
            imported['monthly_volume'] = float(data.total_volume)

        if data.effective_rate and data.effective_rate > 0:
            analysis.current_processing_rate = round(data.effective_rate, 2)
            imported['current_processing_rate'] = float(analysis.current_processing_rate)

        if data.monthly_fees and data.monthly_fees > 0:
            analysis.current_monthly_fees = data.monthly_fees
            imported['current_monthly_fees'] = float(data.monthly_fees)

        if data.transaction_count and data.transaction_count > 0:
            analysis.monthly_transaction_count = data.transaction_count
            imported['monthly_transaction_count'] = data.transaction_count

        if data.interchange_fees and data.interchange_fees > 0:
            analysis.interchange_total = data.interchange_fees
            imported['interchange_total'] = float(data.interchange_fees)

        if data.interac_count and data.interac_count > 0:
            analysis.interac_txn_count = data.interac_count
            imported['interac_txn_count'] = data.interac_count

        if data.visa_volume and data.visa_volume > 0:
            analysis.visa_volume = data.visa_volume
            imported['visa_volume'] = float(data.visa_volume)

        if data.mastercard_volume and data.mastercard_volume > 0:
            analysis.mc_volume = data.mastercard_volume
            imported['mc_volume'] = float(data.mastercard_volume)

        if data.amex_volume and data.amex_volume > 0:
            analysis.amex_volume = data.amex_volume
            imported['amex_volume'] = float(data.amex_volume)

        analysis.save()

        return Response({
            'success': True,
            'analysis_id': analysis.id,
            'fields_imported': imported,
            'message': f'{len(imported)} field(s) imported from statement.',
        }, status=status.HTTP_200_OK)
