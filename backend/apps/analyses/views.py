from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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
