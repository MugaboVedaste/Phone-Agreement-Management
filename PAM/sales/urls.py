from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.sales_dashboard_view, name='sales_dashboard'),
    path('transactions/', views.transaction_list_view, name='transaction_list'),
    path('report/', views.report_view, name='report'),
    path('report/export/', views.report_export_view, name='report_export'),
    path('targets/', views.target_list_view, name='target_list'),
    path('targets/create/', views.target_create_view, name='target_create'),
]
