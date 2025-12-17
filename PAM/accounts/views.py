from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from .models import CustomUser
from agreements.models import Phone, Agreement
from sales.models import SalesTransaction


def register_view(request):
    """
    Seller self-registration view.
    Only sellers can register themselves.
    Manager accounts must be created by superuser.
    New sellers are automatically suspended until manager activates them.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
        
        # Phone number validation
        if not phone_number.startswith('+250') or len(phone_number) != 13:
            messages.error(request, 'Phone number must be in format +250XXXXXXXXX')
            return render(request, 'accounts/register.html')
        
        try:
            # Create seller account (automatically suspended)
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                role='seller'
            )
            
            # Auto-suspend new seller accounts
            user.suspend(
                reason="New account pending manager approval",
                suspended_by=None
            )
            
            messages.success(
                request, 
                'Account created successfully! Your account is pending approval. '
                'Please contact a manager to activate your account.'
            )
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user is suspended (only for non-superusers)
            if not user.is_superuser and user.is_suspended:
                return redirect('hold')
            
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on role
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # Role-based redirect
            if user.is_superuser:
                return redirect('admin:index')
            elif user.is_manager():
                return redirect('manager_dashboard')
            elif user.is_seller():
                return redirect('phone_list')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def hold_view(request):
    """
    Account suspension/hold page.
    Displays suspension information to suspended users.
    """
    if not request.user.is_suspended:
        return redirect('home')
    
    return render(request, 'accounts/hold.html')


@login_required
def home_view(request):
    """
    Home/dashboard view - redirects users based on role.
    Sellers go to inventory, managers to their dashboard.
    """
    # Redirect based on user role
    if request.user.is_superuser:
        return redirect('admin:index')
    if request.user.is_manager():
        return redirect('manager_dashboard')
    if request.user.is_seller():
        return redirect('phone_list')
    
    # Default redirect for other users
    return redirect('phone_list')


@login_required
def manager_dashboard_view(request):
    """
    Manager dashboard with system-wide statistics and management tools.
    Only accessible to managers and superusers.
    """
    # Check permission
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('home')
    
    # Get comprehensive statistics
    context = {
        'stats': {
            'total_sellers': CustomUser.objects.filter(role='seller').count(),
            'active_sellers': CustomUser.objects.filter(role='seller', is_suspended=False).count(),
            'suspended_sellers': CustomUser.objects.filter(role='seller', is_suspended=True).count(),
            'pending_approval': CustomUser.objects.filter(
                role='seller', 
                is_suspended=True,
                suspended_reason__icontains='pending'
            ).count(),
            'total_phones': Phone.objects.count(),
            'available_phones': Phone.objects.filter(status='available').count(),
            'sold_phones': Phone.objects.filter(status='sold').count(),
            'assigned_phones': Phone.objects.filter(status='assigned').count(),
            'total_agreements': Agreement.objects.count(),
            'total_transactions': SalesTransaction.objects.filter(status='completed').count(),
            'monthly_revenue': 0,
            'monthly_profit': 0,
        }
    }
    
    # Monthly financial stats
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_transactions = SalesTransaction.objects.filter(
        sale_date__gte=month_start,
        status='completed'
    )
    
    context['stats']['monthly_revenue'] = monthly_transactions.aggregate(
        total=Sum('sale_price')
    )['total'] or 0
    
    context['stats']['monthly_profit'] = monthly_transactions.aggregate(
        total=Sum('profit')
    )['total'] or 0
    
    # Recent activities
    context['pending_sellers'] = CustomUser.objects.filter(
        role='seller',
        is_suspended=True,
        suspended_reason__icontains='pending'
    ).order_by('-date_joined')[:5]
    
    context['recent_agreements'] = Agreement.objects.select_related(
        'seller', 'phone'
    ).order_by('-created_at')[:10]
    
    context['recent_transactions'] = SalesTransaction.objects.select_related(
        'seller', 'phone'
    ).filter(status='completed').order_by('-sale_date')[:10]
    
    # Top performing sellers
    context['top_sellers'] = SalesTransaction.objects.filter(
        sale_date__gte=month_start,
        status='completed'
    ).values('seller__username', 'seller__first_name', 'seller__last_name').annotate(
        total_sales=Count('id'),
        total_revenue=Sum('sale_price'),
        total_profit=Sum('profit')
    ).order_by('-total_revenue')[:5]
    
    return render(request, 'accounts/manager_dashboard.html', context)


@login_required
def approve_seller_view(request, user_id):
    """
    Approve a pending seller account.
    Only accessible to managers and superusers.
    """
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('home')
    
    seller = get_object_or_404(CustomUser, pk=user_id, role='seller')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            seller.activate()
            messages.success(request, f'Seller {seller.get_full_name()} has been activated successfully!')
        elif action == 'reject':
            reason = request.POST.get('reason', 'Account rejected by manager')
            seller.suspend(reason=reason, suspended_by=request.user)
            messages.warning(request, f'Seller {seller.get_full_name()} has been rejected.')
        
        return redirect('pending_sellers')
    
    context = {
        'seller': seller,
    }
    return render(request, 'accounts/approve_seller.html', context)


@login_required
def pending_sellers_view(request):
    """
    List all pending sellers awaiting approval.
    Only accessible to managers and superusers.
    """
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('home')
    
    pending_sellers = CustomUser.objects.filter(
        role='seller',
        is_suspended=True,
        suspended_reason__icontains='pending'
    ).order_by('-date_joined')
    
    context = {
        'pending_sellers': pending_sellers,
    }
    return render(request, 'accounts/pending_sellers.html', context)


@login_required
def manage_sellers_view(request):
    """
    Manage all sellers (view, suspend, activate).
    Only accessible to managers and superusers.
    """
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('home')
    
    sellers = CustomUser.objects.filter(role='seller').order_by('-date_joined')
    
    # Apply filters
    status = request.GET.get('status')
    if status == 'active':
        sellers = sellers.filter(is_suspended=False)
    elif status == 'suspended':
        sellers = sellers.filter(is_suspended=True)
    
    context = {
        'sellers': sellers,
    }
    return render(request, 'accounts/manage_sellers.html', context)


@login_required
def toggle_seller_status_view(request, user_id):
    """
    Toggle seller active/suspended status.
    Only accessible to managers and superusers.
    """
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('home')
    
    seller = get_object_or_404(CustomUser, pk=user_id, role='seller')
    
    if seller.is_suspended:
        seller.activate()
        messages.success(request, f'{seller.get_full_name()} has been activated.')
    else:
        reason = request.POST.get('reason', 'Suspended by manager')
        seller.suspend(reason=reason, suspended_by=request.user)
        messages.warning(request, f'{seller.get_full_name()} has been suspended.')
    
    return redirect('manage_sellers')


@login_required
def profile_view(request):
    """
    User profile view and edit.
    Allows users to update their personal information and signature.
    """
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.phone_number = request.POST.get('phone_number', '').strip()
        request.user.address = request.POST.get('address', '').strip()
        request.user.national_id = request.POST.get('national_id', '').strip()
        
        # Handle signature upload
        if 'signature' in request.FILES:
            request.user.signature = request.FILES['signature']
        
        request.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })
