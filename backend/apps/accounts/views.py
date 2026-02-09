from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UserProfileUpdateSerializer,
    CreateAdminSerializer,
    CreateAgentSerializer
)
from .permissions import IsAdmin, IsAdminOrAgent, IsSuperUser
from .models import UserProfile

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration (DISABLED - Use admin endpoints instead)
    POST /api/v1/auth/register/

    Note: Public registration is disabled. Users must be created by:
    - Superuser creates Admin via /api/v1/auth/admin/create-admin/
    - Admin creates Agent via /api/v1/auth/admin/create-agent/
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Disable public registration
        return Response({
            'error': 'Public registration is disabled',
            'message': 'Please contact an administrator to create your account'
        }, status=status.HTTP_403_FORBIDDEN)


class LoginView(APIView):
    """
    API endpoint for user login
    POST /api/v1/auth/login/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Update last login IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Return user data with tokens
        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    API endpoint for user logout
    POST /api/v1/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Logout successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to get and update user profile
    GET /api/v1/auth/profile/
    PUT /api/v1/auth/profile/
    PATCH /api/v1/auth/profile/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Update user fields
        user_data = {}
        for field in ['first_name', 'last_name', 'phone', 'organization', 'email']:
            if field in request.data:
                user_data[field] = request.data[field]

        if user_data:
            serializer = self.get_serializer(instance, data=user_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        # Update profile fields
        profile_data = {}
        for field in ['avatar', 'bio', 'preferred_language', 'timezone', 'notification_preferences']:
            if field in request.data:
                profile_data[field] = request.data[field]

        if profile_data and hasattr(instance, 'profile'):
            profile_serializer = UserProfileUpdateSerializer(
                instance.profile,
                data=profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        # Return updated user data
        serializer = self.get_serializer(instance)
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        })


class ChangePasswordView(APIView):
    """
    API endpoint to change password
    POST /api/v1/auth/password/change/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    API endpoint to list all users (Admin only)
    GET /api/v1/auth/users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'username', 'email']


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to get, update, or delete a specific user (Admin only)
    GET /api/v1/auth/users/{id}/
    PUT /api/v1/auth/users/{id}/
    DELETE /api/v1/auth/users/{id}/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Prevent admin from deleting themselves
        if instance == request.user:
            return Response({
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response({
            'message': 'User deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class CreateAdminView(generics.CreateAPIView):
    """
    API endpoint for superuser to create admin users
    POST /api/v1/auth/admin/create-admin/

    Requires: Django superuser (is_superuser=True)
    """
    queryset = User.objects.all()
    serializer_class = CreateAdminSerializer
    permission_classes = [IsSuperUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return user data without tokens (admin creates, doesn't auto-login)
        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'message': 'Admin user created successfully'
        }, status=status.HTTP_201_CREATED)


class CreateAgentView(generics.CreateAPIView):
    """
    API endpoint for admin to create agent users
    POST /api/v1/auth/admin/create-agent/

    Requires: Admin role (role='ADMIN') or Superuser
    """
    queryset = User.objects.all()
    serializer_class = CreateAgentSerializer
    permission_classes = [IsAdmin | IsSuperUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return user data without tokens (admin creates, doesn't auto-login)
        user_serializer = UserSerializer(user)
        return Response({
            'user': user_serializer.data,
            'message': 'Agent user created successfully'
        }, status=status.HTTP_201_CREATED)
