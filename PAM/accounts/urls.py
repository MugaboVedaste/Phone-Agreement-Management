from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('hold/', views.hold_view, name='hold'),
    path('profile/', views.profile_view, name='profile'),
    
    # Manager routes
    path('manager/dashboard/', views.manager_dashboard_view, name='manager_dashboard'),
    path('manager/sellers/pending/', views.pending_sellers_view, name='pending_sellers'),
    path('manager/sellers/', views.manage_sellers_view, name='manage_sellers'),
    path('manager/sellers/<int:user_id>/approve/', views.approve_seller_view, name='approve_seller'),
    path('manager/sellers/<int:user_id>/toggle/', views.toggle_seller_status_view, name='toggle_seller_status'),
]
