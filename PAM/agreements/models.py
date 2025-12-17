from django.db import models
from django.utils import timezone
from accounts.models import CustomUser


class Phone(models.Model):
    """
    Phone model representing individual phones in inventory.
    Tracks phone details, ownership, and status throughout lifecycle.
    """
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('assigned', 'Assigned'),
    ]
    
    # Unique identifiers
    imei = models.CharField(max_length=15, unique=True, db_index=True,
                           help_text='15-digit IMEI number')
    serial_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Phone specifications
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used')
    
    # Status and ownership
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_owner = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='owned_phones',
        help_text='Current owner/seller of this phone'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Phone'
        verbose_name_plural = 'Phones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['imei', 'serial_number']),
            models.Index(fields=['status', 'current_owner']),
        ]
    
    def __str__(self):
        return f"{self.brand} {self.model} - IMEI: {self.imei}"
    
    def is_available(self):
        """Check if phone is available for sale or assignment"""
        return self.status == 'available'
    
    def mark_as_sold(self):
        """Mark phone as sold"""
        self.status = 'sold'
        self.save()
    
    def mark_as_assigned(self):
        """Mark phone as assigned to another seller"""
        self.status = 'assigned'
        self.save()
    
    def mark_as_available(self):
        """Mark phone as available"""
        self.status = 'available'
        self.save()


class Agreement(models.Model):
    """
    Agreement model for buy/sell transactions.
    Captures customer/seller information and documents.
    """
    AGREEMENT_TYPE_CHOICES = [
        ('buy', 'Buy Agreement'),
        ('sell', 'Sell Agreement'),
    ]
    
    # Agreement details
    agreement_type = models.CharField(max_length=4, choices=AGREEMENT_TYPE_CHOICES)
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='agreements')
    seller = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='agreements',
        help_text='Seller/dealer creating this agreement'
    )
    
    # Customer/Previous owner information
    customer_name = models.CharField(max_length=100)
    customer_national_id = models.CharField(max_length=30)
    customer_phone = models.CharField(max_length=15, help_text='Format: 07XXXXXXXX')
    customer_address = models.TextField()
    
    # Document capture (photos)
    id_photo = models.ImageField(upload_to='agreements/id_photos/', blank=True, null=True)
    passport_photo = models.ImageField(upload_to='agreements/passport_photos/', blank=True, null=True)
    
    # Digital signature (dual storage: base64 + image file)
    signature = models.TextField(blank=True, help_text='Base64 canvas signature data')
    signature_photo = models.ImageField(upload_to='agreements/signatures/', blank=True, null=True,
                                       help_text='Signature image file for PDF')
    
    # Transaction details
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Agreement'
        verbose_name_plural = 'Agreements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agreement_type', 'seller']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_agreement_type_display()} - {self.phone.imei} - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def agreement_number(self):
        """Generate agreement number matching PDF format"""
        return f"AGR-{str(self.id).zfill(6)}"
    
    @property
    def agreed_price(self):
        """Alias for price field for template compatibility"""
        return self.price
    
    def is_buy_agreement(self):
        """Check if this is a buy agreement"""
        return self.agreement_type == 'buy'
    
    def is_sell_agreement(self):
        """Check if this is a sell agreement"""
        return self.agreement_type == 'sell'


class PhoneHistory(models.Model):
    """
    Immutable audit trail for phone transactions.
    Records all actions performed on a phone (buy, sell, assign, approve, reject).
    NEVER delete or modify records - append-only for legal compliance.
    """
    ACTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('assign', 'Assign'),
        ('approve', 'Approve Assignment'),
        ('reject', 'Reject Assignment'),
    ]
    
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    
    # Users involved in the action
    from_user = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='actions_from',
        help_text='User initiating the action'
    )
    to_user = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='actions_to',
        help_text='User receiving (for assignments)'
    )
    
    # Related agreement (if applicable)
    agreement = models.ForeignKey(
        Agreement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='history_entries'
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Phone History'
        verbose_name_plural = 'Phone Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.phone.imei} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class PhoneAssignment(models.Model):
    """
    Phone assignment model for peer-to-peer transfers between sellers.
    Tracks pending, approved, and rejected assignment requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name='assignments')
    from_seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='assignments_sent',
        help_text='Seller assigning the phone'
    )
    to_seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='assignments_received',
        help_text='Seller receiving the phone'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text='Optional message for the recipient')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Phone Assignment'
        verbose_name_plural = 'Phone Assignments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'to_seller']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.phone.imei} - {self.from_seller.username} → {self.to_seller.username} ({self.status})"
    
    def is_pending(self):
        """Check if assignment is pending"""
        return self.status == 'pending'
    
    def approve(self):
        """Approve the assignment and transfer ownership"""
        self.status = 'approved'
        self.phone.current_owner = self.to_seller
        self.phone.status = 'available'
        self.phone.save()
        self.save()
        
        # Create history entry
        PhoneHistory.objects.create(
            phone=self.phone,
            action='approve',
            from_user=self.from_seller,
            to_user=self.to_seller,
            notes=f'Assignment approved: {self.phone.imei} transferred from {self.from_seller.username} to {self.to_seller.username}'
        )
    
    def reject(self):
        """Reject the assignment and revert phone status"""
        self.status = 'rejected'
        self.phone.status = 'available'
        self.phone.save()
        self.save()
        
        # Create history entry
        PhoneHistory.objects.create(
            phone=self.phone,
            action='reject',
            from_user=self.to_seller,
            to_user=self.from_seller,
            notes=f'Assignment rejected: {self.phone.imei} assignment from {self.from_seller.username} to {self.to_seller.username} was rejected'
        )
