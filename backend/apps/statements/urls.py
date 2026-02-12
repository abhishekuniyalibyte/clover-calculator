from django.urls import path
from .views import (
    FileUploadView,
    ManualEntryView,
    StatementListView,
    StatementDetailView,
    StatementReviewView,
)

app_name = 'statements'

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload'),
    path('manual/', ManualEntryView.as_view(), name='manual'),
    path('', StatementListView.as_view(), name='list'),
    path('<int:pk>/', StatementDetailView.as_view(), name='detail'),
    path('<int:pk>/review/', StatementReviewView.as_view(), name='review'),
]
