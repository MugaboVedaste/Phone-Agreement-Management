from django.db import models
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from decimal import Decimal
from accounts.models import CustomUser
from agreements.models import Phone, Agreement


class SalesTransaction(models.Model):
    """
    Individual sales transaction record.
    Tracks each phone sale made by a seller.
    """
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit', 'Credit'),
        ('other', 'Other'),
    ]
    
    # Transaction details
    transaction_id = models.CharField(max_length=50, unique=True, db_index=True,
                                     help_text='Unique transaction identifier')
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sales_transactions',
        limit_choices_to={'role': 'seller'},
        help_text='Seller who made this sale'
    )
    phone = models.ForeignKey(
        Phone,
        on_delete=models.PROTECT,
        related_name='sales_transactions',
        help_text='Phone that was sold'
    )
    agreement = models.OneToOneField(
        Agreement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_transaction',
        help_text='Associated sell agreement'
    )
    
    # Customer information
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField(blank=True)
    
    # Financial details
    sale_price = models.DecimalField(max_digits=10, decimal_places=2,
                                     help_text='Final sale price')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2,
                                     help_text='Purchase/cost price')
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                 help_text='Profit = Sale Price - Cost Price')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                         help_text='Commission percentage')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text='Commission earned by seller')
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_reference = models.CharField(max_length=100, blank=True,
                                        help_text='Payment reference/receipt number')
    
    # Status and tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    
    # Timestamps
    sale_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sales Transaction'
        verbose_name_plural = 'Sales Transactions'
        ordering = ['-sale_date']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['seller', '-sale_date']),
            models.Index(fields=['status', '-sale_date']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.seller.username} - {self.phone.brand} {self.phone.model}"
    
    def save(self, *args, **kwargs):
        """Calculate profit and commission before saving"""
        if self.sale_price and self.cost_price:
            self.profit = self.sale_price - self.cost_price
            self.commission_amount = (self.profit * self.commission_rate) / 100
        
        # Generate transaction ID if not provided
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Generate unique transaction ID"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"TXN-{timestamp}-{self.seller.id}"
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price and self.cost_price > 0:
            return (self.profit / self.cost_price) * 100
        return 0


class SellerPerformance(models.Model):
    """
    Tracks seller performance metrics over time.
    Aggregates sales data for reporting and analytics.
    """
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='performance_records',
        limit_choices_to={'role': 'seller'}
    )
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Sales metrics
    total_sales = models.IntegerField(default=0, help_text='Total number of sales')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                       help_text='Total sales revenue')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Performance indicators
    average_sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                               help_text='Average profit margin %')
    
    # Rankings
    rank_in_period = models.IntegerField(null=True, blank=True,
                                        help_text='Seller rank compared to others')
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Seller Performance'
        verbose_name_plural = 'Seller Performance Records'
        ordering = ['-period_start', '-total_revenue']
        unique_together = ['seller', 'period_type', 'period_start']
        indexes = [
            models.Index(fields=['seller', 'period_type', '-period_start']),
        ]
    
    def __str__(self):
        return f"{self.seller.username} - {self.period_type} ({self.period_start} to {self.period_end})"
    
    @classmethod
    def calculate_performance(cls, seller, period_type, start_date, end_date):
        """
        Calculate and save performance metrics for a seller in a given period.
        """
        transactions = SalesTransaction.objects.filter(
            seller=seller,
            status='completed',
            sale_date__gte=start_date,
            sale_date__lte=end_date
        )
        
        metrics = transactions.aggregate(
            total_sales=Count('id'),
            total_revenue=Sum('sale_price'),
            total_cost=Sum('cost_price'),
            total_profit=Sum('profit'),
            total_commission=Sum('commission_amount'),
            avg_sale_price=Avg('sale_price')
        )
        
        # Create or update performance record
        performance, created = cls.objects.update_or_create(
            seller=seller,
            period_type=period_type,
            period_start=start_date,
            defaults={
                'period_end': end_date,
                'total_sales': metrics['total_sales'] or 0,
                'total_revenue': metrics['total_revenue'] or 0,
                'total_cost': metrics['total_cost'] or 0,
                'total_profit': metrics['total_profit'] or 0,
                'total_commission': metrics['total_commission'] or 0,
                'average_sale_price': metrics['avg_sale_price'] or 0,
            }
        )
        
        # Calculate average profit margin
        if performance.total_cost and performance.total_cost > 0:
            performance.average_profit_margin = (performance.total_profit / performance.total_cost) * 100
            performance.save()
        
        return performance


class SalesTarget(models.Model):
    """
    Sales targets/goals for sellers.
    Used for performance evaluation and incentives.
    """
    TARGET_TYPE_CHOICES = [
        ('sales_count', 'Number of Sales'),
        ('revenue', 'Revenue Target'),
        ('profit', 'Profit Target'),
    ]
    
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sales_targets',
        limit_choices_to={'role': 'seller'}
    )
    target_type = models.CharField(max_length=15, choices=TARGET_TYPE_CHOICES)
    target_value = models.DecimalField(max_digits=12, decimal_places=2,
                                      help_text='Target value to achieve')
    achieved_value = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                        help_text='Current achieved value')
    
    # Period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    is_active = models.BooleanField(default=True)
    is_achieved = models.BooleanField(default=False)
    achievement_date = models.DateTimeField(null=True, blank=True)
    
    # Incentive
    incentive_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                          help_text='Bonus for achieving target')
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Sales Target'
        verbose_name_plural = 'Sales Targets'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.seller.username} - {self.get_target_type_display()} - {self.target_value}"
    
    def get_achievement_percentage(self):
        """Calculate achievement percentage"""
        if self.target_value and self.target_value > 0:
            return (self.achieved_value / self.target_value) * 100
        return 0
    
    def check_achievement(self):
        """Check if target is achieved and update status"""
        if self.achieved_value >= self.target_value and not self.is_achieved:
            self.is_achieved = True
            self.achievement_date = timezone.now()
            self.save()
    
    def update_progress(self):
        """Update achieved value based on actual sales"""
        if not self.is_active:
            return
        
        transactions = SalesTransaction.objects.filter(
            seller=self.seller,
            status='completed',
            sale_date__gte=self.start_date,
            sale_date__lte=self.end_date
        )
        
        if self.target_type == 'sales_count':
            self.achieved_value = transactions.count()
        elif self.target_type == 'revenue':
            self.achieved_value = transactions.aggregate(
                total=Sum('sale_price')
            )['total'] or 0
        elif self.target_type == 'profit':
            self.achieved_value = transactions.aggregate(
                total=Sum('profit')
            )['total'] or 0
        
        self.save()
        self.check_achievement()


class Customer(models.Model):
    """
    Customer database for tracking repeat customers and sales history.
    """
    # Customer information
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    
    # Customer metrics
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_purchase_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Seller who first registered this customer
    registered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_customers',
        limit_choices_to={'role': 'seller'}
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    first_purchase_date = models.DateTimeField(null=True, blank=True)
    last_purchase_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-last_purchase_date']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['-last_purchase_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.phone}"
    
    def update_metrics(self):
        """Update customer purchase metrics"""
        transactions = SalesTransaction.objects.filter(
            customer_phone=self.phone,
            status='completed'
        )
        
        self.total_purchases = transactions.count()
        total_spent = transactions.aggregate(total=Sum('sale_price'))['total'] or 0
        self.total_spent = total_spent
        
        if self.total_purchases > 0:
            self.average_purchase_value = self.total_spent / self.total_purchases
        
        # Update purchase dates
        if transactions.exists():
            self.first_purchase_date = transactions.order_by('sale_date').first().sale_date
            self.last_purchase_date = transactions.order_by('-sale_date').first().sale_date
        
        self.save()
