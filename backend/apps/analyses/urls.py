from django.urls import path
from .views import (
    MerchantListCreateView,
    MerchantDetailView,
    CompetitorListView,
    CompetitorCreateView,
    CompetitorDetailView,
    AnalysisListCreateView,
    AnalysisDetailView,
    MerchantHardwareListCreateView,
    MerchantHardwareDetailView,
    PricingModelListCreateView,
    PricingModelDetailView,
    DeviceCatalogListView,
    DeviceCatalogCreateView,
    DeviceCatalogDetailView,
    ProposedDeviceListCreateView,
    ProposedDeviceDetailView,
    SaaSCatalogListView,
    SaaSCatalogCreateView,
    SaaSCatalogDetailView,
    ProposedSaaSListCreateView,
    ProposedSaaSDetailView,
    OneTimeFeeListCreateView,
    OneTimeFeeDetailView,
    AnalysisCalculateView,
    AnalysisImportFromStatementView,
    AnalysisSummaryView,
    CostBreakdownView,
    ProposalPreviewView,
)

app_name = 'analyses'

urlpatterns = [
    # Merchant endpoints
    path('merchants/', MerchantListCreateView.as_view(), name='merchant_list_create'),
    path('merchants/<int:pk>/', MerchantDetailView.as_view(), name='merchant_detail'),

    # Competitor endpoints
    path('competitors/', CompetitorListView.as_view(), name='competitor_list'),
    path('competitors/create/', CompetitorCreateView.as_view(), name='competitor_create'),
    path('competitors/<int:pk>/', CompetitorDetailView.as_view(), name='competitor_detail'),

    # Analysis endpoints
    path('', AnalysisListCreateView.as_view(), name='analysis_list_create'),
    path('<int:pk>/', AnalysisDetailView.as_view(), name='analysis_detail'),
    path('<int:pk>/calculate/', AnalysisCalculateView.as_view(), name='analysis_calculate'),
    path('<int:pk>/import-from-statement/', AnalysisImportFromStatementView.as_view(), name='analysis_import_from_statement'),
    path('<int:pk>/summary/', AnalysisSummaryView.as_view(), name='analysis_summary'),
    path('<int:pk>/cost-breakdown/', CostBreakdownView.as_view(), name='analysis_cost_breakdown'),
    path('<int:pk>/proposal-preview/', ProposalPreviewView.as_view(), name='analysis_proposal_preview'),

    # Merchant Hardware endpoints
    path('hardware/', MerchantHardwareListCreateView.as_view(), name='hardware_list_create'),
    path('hardware/<int:pk>/', MerchantHardwareDetailView.as_view(), name='hardware_detail'),

    # Pricing Model endpoints
    path('pricing-models/', PricingModelListCreateView.as_view(), name='pricing_model_list_create'),
    path('pricing-models/<int:pk>/', PricingModelDetailView.as_view(), name='pricing_model_detail'),

    # Device Catalog endpoints (Admin-managed)
    path('catalog/devices/', DeviceCatalogListView.as_view(), name='device_catalog_list'),
    path('catalog/devices/create/', DeviceCatalogCreateView.as_view(), name='device_catalog_create'),
    path('catalog/devices/<int:pk>/', DeviceCatalogDetailView.as_view(), name='device_catalog_detail'),

    # Proposed Device endpoints
    path('proposed-devices/', ProposedDeviceListCreateView.as_view(), name='proposed_device_list_create'),
    path('proposed-devices/<int:pk>/', ProposedDeviceDetailView.as_view(), name='proposed_device_detail'),

    # SaaS Catalog endpoints (Admin-managed)
    path('catalog/saas/', SaaSCatalogListView.as_view(), name='saas_catalog_list'),
    path('catalog/saas/create/', SaaSCatalogCreateView.as_view(), name='saas_catalog_create'),
    path('catalog/saas/<int:pk>/', SaaSCatalogDetailView.as_view(), name='saas_catalog_detail'),

    # Proposed SaaS endpoints
    path('proposed-saas/', ProposedSaaSListCreateView.as_view(), name='proposed_saas_list_create'),
    path('proposed-saas/<int:pk>/', ProposedSaaSDetailView.as_view(), name='proposed_saas_detail'),

    # One-Time Fee endpoints
    path('onetime-fees/', OneTimeFeeListCreateView.as_view(), name='onetime_fee_list_create'),
    path('onetime-fees/<int:pk>/', OneTimeFeeDetailView.as_view(), name='onetime_fee_detail'),
]
