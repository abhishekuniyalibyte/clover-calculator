from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    CreateAdminView,
    CreateAgentView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile management
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),

    # User management (Admin only)
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),

    # User creation with hierarchy (Superuser/Admin only)
    path('admin/create-admin/', CreateAdminView.as_view(), name='create_admin'),
    path('admin/create-agent/', CreateAgentView.as_view(), name='create_agent'),
]
