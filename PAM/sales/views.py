from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import SalesTransaction, SellerPerformance, SalesTarget, Customer
from accounts.models import CustomUser
import json


@login_required
def sales_dashboard_view(request):
    """Main sales dashboard with analytics"""
    # Get period filter from request
    period = request.GET.get('period', 'all')
    start_date_param = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    # Filter transactions by role first - NO date filter by default
    if request.user.is_seller():
        transactions = SalesTransaction.objects.filter(seller=request.user)
    else:
        transactions = SalesTransaction.objects.all()
    
    # Only apply date filter if user explicitly provides dates
    start_date = None
    end_date = None
    
    if start_date_param and end_date_param:
        # User provided explicit date range
        if isinstance(start_date_param, str):
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
        if isinstance(end_date_param, str):
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        transactions = transactions.filter(sale_date__date__range=[start_date, end_date])
    elif period != 'all':
        # Apply period-based filter only if period is selected
        if period == 'daily':
            start_date = datetime.now().date()
        elif period == 'weekly':
            start_date = datetime.now().date() - timedelta(days=7)
        elif period == 'monthly':
            start_date = datetime.now().replace(day=1).date()
        elif period == 'quarterly':
            start_date = datetime.now().replace(month=((datetime.now().month-1)//3)*3+1, day=1).date()
        else:  # yearly
            start_date = datetime.now().replace(month=1, day=1).date()
        
        end_date = datetime.now().date()
        transactions = transactions.filter(sale_date__date__range=[start_date, end_date])
    
    # Calculate statistics
    stats = {
        'total_sales': transactions.count(),
        'total_revenue': transactions.aggregate(
            total=Sum('sale_price'))['total'] or 0,
        'total_profit': transactions.aggregate(
            total=Sum('profit'))['total'] or 0,
        'avg_sale_price': transactions.aggregate(
            avg=Avg('sale_price'))['avg'] or 0,
        'sales_growth': 0,  # TODO: Calculate growth
        'revenue_growth': 0,  # TODO: Calculate growth
        'profit_margin': 0,
    }
    
    # Calculate profit margin
    if stats['total_revenue'] > 0:
        stats['profit_margin'] = (stats['total_profit'] / stats['total_revenue']) * 100
    
    # Recent transactions
    recent_transactions = transactions.order_by('-sale_date')[:10]
    
    # Top performers
    if request.user.is_manager() or request.user.is_superuser:
        if start_date and end_date:
            top_performers = SellerPerformance.objects.filter(
                period_start__gte=start_date,
                period_end__lte=end_date
            ).select_related('seller').order_by('-total_revenue')[:5]
        else:
            # Show all-time top performers when no date filter
            top_performers = SellerPerformance.objects.select_related('seller').order_by('-total_revenue')[:5]
    else:
        top_performers = []
    
    # Active targets
    if request.user.is_seller():
        active_targets = SalesTarget.objects.filter(
            seller=request.user,
            is_active=True,
            end_date__gte=datetime.now().date()
        )[:5]
    else:
        # Managers see all active targets
        active_targets = SalesTarget.objects.filter(
            is_active=True,
            end_date__gte=datetime.now().date()
        )[:5]
    
    # Chart data
    chart_labels = []
    chart_revenue = []
    chart_profit = []
    
    # Generate chart data based on period
    if period == 'all':
        # Last 6 months for "All Time" view
        for i in range(6):
            date = datetime.now().replace(day=1) - timedelta(days=30*(5-i))
            chart_labels.append(date.strftime('%b %Y'))
            
            month_data = transactions.filter(
                sale_date__year=date.year,
                sale_date__month=date.month
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(month_data['revenue'] or 0))
            chart_profit.append(float(month_data['profit'] or 0))
    elif period == 'daily':
        # Last 7 days
        for i in range(7):
            date = datetime.now().date() - timedelta(days=6-i)
            chart_labels.append(date.strftime('%b %d'))
            
            day_data = transactions.filter(
                sale_date__date=date
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(day_data['revenue'] or 0))
            chart_profit.append(float(day_data['profit'] or 0))
    elif period == 'weekly':
        # Last 4 weeks
        for i in range(4):
            end_date_week = datetime.now().date() - timedelta(days=7*i)
            start_date_week = end_date_week - timedelta(days=6)
            chart_labels.append(f"{start_date_week.strftime('%b %d')} - {end_date_week.strftime('%b %d')}")
            
            week_data = transactions.filter(
                sale_date__date__range=[start_date_week, end_date_week]
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(week_data['revenue'] or 0))
            chart_profit.append(float(week_data['profit'] or 0))
        # Reverse to show oldest to newest
        chart_labels.reverse()
        chart_revenue.reverse()
        chart_profit.reverse()
    elif period == 'monthly':
        # Last 6 months
        for i in range(6):
            date = datetime.now().replace(day=1) - timedelta(days=30*(5-i))
            chart_labels.append(date.strftime('%b %Y'))
            
            month_data = transactions.filter(
                sale_date__year=date.year,
                sale_date__month=date.month
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(month_data['revenue'] or 0))
            chart_profit.append(float(month_data['profit'] or 0))
    elif period == 'quarterly':
        # Last 4 quarters
        for i in range(4):
            months_back = (3-i) * 3
            date = datetime.now().replace(day=1) - timedelta(days=90*months_back)
            quarter = ((date.month-1)//3) + 1
            chart_labels.append(f"Q{quarter} {date.year}")
            
            # Get start and end of quarter
            quarter_start_month = (quarter - 1) * 3 + 1
            quarter_end_month = quarter * 3
            
            quarter_data = transactions.filter(
                sale_date__year=date.year,
                sale_date__month__gte=quarter_start_month,
                sale_date__month__lte=quarter_end_month
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(quarter_data['revenue'] or 0))
            chart_profit.append(float(quarter_data['profit'] or 0))
    elif period == 'yearly':
        # Last 3 years
        current_year = datetime.now().year
        for i in range(3):
            year = current_year - (2-i)
            chart_labels.append(str(year))
            
            year_data = transactions.filter(
                sale_date__year=year
            ).aggregate(
                revenue=Sum('sale_price'),
                profit=Sum('profit')
            )
            chart_revenue.append(float(year_data['revenue'] or 0))
            chart_profit.append(float(year_data['profit'] or 0))
    
    # All transactions for the table below dashboard
    all_transactions = transactions.select_related('seller', 'phone', 'agreement').order_by('-sale_date')
    
    # Pagination for all transactions
    paginator = Paginator(all_transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all sellers for filter (managers only)
    sellers = CustomUser.objects.filter(role='seller', is_suspended=False) if (request.user.is_manager() or request.user.is_superuser) else []
    
    context = {
        'stats': stats,
        'recent_transactions': recent_transactions,
        'top_performers': top_performers,
        'active_targets': active_targets,
        'chart_labels': json.dumps(chart_labels),
        'chart_revenue': json.dumps(chart_revenue),
        'chart_profit': json.dumps(chart_profit),
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'all_transactions': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'sellers': sellers,
    }
    
    return render(request, 'sales/dashboard.html', context)


@login_required
def transaction_list_view(request):
    """List all transactions"""
    transactions = SalesTransaction.objects.all().select_related(
        'seller', 'phone', 'agreement'
    ).order_by('-sale_date')
    
    # Filter by seller if not manager
    if request.user.is_seller():
        transactions = transactions.filter(seller=request.user)
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)
    
    seller_id = request.GET.get('seller')
    if seller_id and (request.user.is_manager() or request.user.is_superuser):
        transactions = transactions.filter(seller_id=seller_id)
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    
    return render(request, 'sales/transaction_list.html', context)


@login_required
def report_view(request):
    """Generate sales reports"""
    report_type = request.GET.get('report_type', 'summary')
    start_date = request.GET.get('start_date', datetime.now().replace(day=1).date())
    end_date = request.GET.get('end_date', datetime.now().date())
    
    # Convert string dates if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get transactions
    transactions = SalesTransaction.objects.filter(
        sale_date__range=[start_date, end_date],
        status='completed'
    ).select_related('seller', 'phone')
    
    # Filter by seller if not manager
    if request.user.is_seller():
        transactions = transactions.filter(seller=request.user)
    
    # Calculate report data
    report = {
        'total_transactions': transactions.count(),
        'total_revenue': transactions.aggregate(Sum('sale_price'))['sale_price__sum'] or 0,
        'total_cost': transactions.aggregate(Sum('cost_price'))['cost_price__sum'] or 0,
        'total_profit': transactions.aggregate(Sum('profit'))['profit__sum'] or 0,
        'total_commission': transactions.aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
        'profit_margin': 0,
    }
    
    if report['total_revenue'] > 0:
        report['profit_margin'] = (report['total_profit'] / report['total_revenue']) * 100
    
    # Seller performance breakdown
    seller_performances = []
    if report_type == 'seller_performance':
        seller_performances = transactions.values('seller__username', 'seller__first_name', 'seller__last_name').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('sale_price'),
            total_profit=Sum('profit'),
            total_commission=Sum('commission_amount'),
            average_profit_margin=Avg('profit') * 100
        )
    
    context = {
        'report': report,
        'transactions': transactions[:100],  # Limit for display
        'seller_performances': seller_performances,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'current_date': datetime.now(),
    }
    
    return render(request, 'sales/report.html', context)


@login_required
def report_export_view(request):
    """Export report to PDF or Excel (placeholder)"""
    format_type = request.GET.get('format', 'pdf')
    
    # TODO: Implement actual export functionality
    messages.info(request, f'{format_type.upper()} export feature coming soon!')
    return redirect('report')


@login_required
def target_list_view(request):
    """List and manage sales targets"""
    targets = SalesTarget.objects.all().select_related('seller').order_by('-created_at')
    
    # Filter by seller if not manager
    if request.user.is_seller():
        targets = targets.filter(seller=request.user)
    
    context = {
        'targets': targets,
    }
    
    return render(request, 'sales/target_list.html', context)


@login_required
def target_create_view(request):
    """Create a new sales target"""
    if not (request.user.is_manager() or request.user.is_superuser):
        messages.error(request, 'Only managers can create sales targets.')
        return redirect('target_list')
    
    if request.method == 'POST':
        try:
            seller_id = request.POST.get('seller')
            seller = get_object_or_404(CustomUser, pk=seller_id, role='seller') if seller_id else None
            
            target = SalesTarget.objects.create(
                seller=seller,
                target_type=request.POST.get('target_type'),
                target_value=request.POST.get('target_value'),
                period_type=request.POST.get('period_type'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                description=request.POST.get('description', '')
            )
            
            messages.success(request, 'Sales target created successfully!')
            return redirect('target_list')
            
        except Exception as e:
            messages.error(request, f'Error creating target: {str(e)}')
    
    sellers = CustomUser.objects.filter(role='seller', is_suspended=False)
    
    context = {
        'sellers': sellers,
    }
    
    return render(request, 'sales/target_form.html', context)
