from django.urls import path
from .views import (
    MerchantListCreateView,
    MerchantDetailView,
    CompetitorListView,
    CompetitorCreateView,
    CompetitorDetailView,
    AnalysisListCreateView,
    AnalysisDetailView,
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
]
