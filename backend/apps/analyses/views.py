from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Merchant, Competitor, Analysis
from .serializers import (
    MerchantSerializer,
    CompetitorSerializer,
    AnalysisListSerializer,
    AnalysisDetailSerializer,
    AnalysisCreateUpdateSerializer
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
