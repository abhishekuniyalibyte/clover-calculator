from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Custom user model with role-based access"""

    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('AGENT', 'Sales Agent'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='AGENT',
        help_text='User role determines access level'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    organization = models.CharField(max_length=255, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """Check if user is an administrator"""
        return self.role == 'ADMIN'

    @property
    def is_agent(self):
        """Check if user is a sales agent"""
        return self.role == 'AGENT'


class UserProfile(models.Model):
    """Extended user profile information"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    bio = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=5, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preferences = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'accounts_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile of {self.user.username}"
