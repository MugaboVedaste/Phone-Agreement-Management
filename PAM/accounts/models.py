from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Supports two roles: seller and manager.
    Includes suspension system for account management.
    """
    ROLE_CHOICES = [
        ('seller', 'Seller'),
        ('manager', 'Manager'),
    ]
    
    # User role and profile information
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=True, null=True, 
                           help_text='Role for regular users. Superusers do not need a role.')
    phone_number = models.CharField(max_length=15, blank=True, help_text='Format: 07XXXXXXXX')
    address = models.TextField(blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True, 
                                  help_text='Profile signature for agreements')
    national_id = models.CharField(max_length=30, blank=True)
    
    # Suspension system fields
    is_suspended = models.BooleanField(default=False, help_text='Account suspension status')
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspended_reason = models.TextField(blank=True, help_text='Reason for suspension')
    suspended_by = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name='suspended_users',
        help_text='Manager who suspended this user'
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_seller(self):
        """Check if user is a seller"""
        return self.role == 'seller'
    
    def is_manager(self):
        """Check if user is a manager"""
        return self.role == 'manager'
    
    def suspend(self, reason, suspended_by=None):
        """Suspend this user account"""
        self.is_suspended = True
        self.suspended_at = timezone.now()
        self.suspended_reason = reason
        self.suspended_by = suspended_by
        self.save()
    
    def activate(self):
        """Activate this user account"""
        self.is_suspended = False
        self.suspended_at = None
        self.suspended_reason = ''
        self.suspended_by = None
        self.save()
