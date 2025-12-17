from django.urls import path
from . import views

urlpatterns = [
    # Phone URLs
    path('phones/', views.phone_list_view, name='phone_list'),
    
    # Combined Buy Phone + Agreement
    path('buy-phone/', views.buy_phone_view, name='buy_phone'),
    
    # Sell Phone (existing phone)
    path('phones/<int:phone_id>/sell/', views.sell_phone_view, name='sell_phone'),
    
    # Agreement URLs
    path('agreements/', views.agreement_list_view, name='agreement_list'),
    path('agreements/<int:pk>/', views.agreement_detail_view, name='agreement_detail'),
    path('agreements/<int:pk>/pdf/', views.agreement_pdf_view, name='agreement_pdf'),
    
    # Phone Assignment URLs
    path('phones/<int:phone_id>/assign/', views.assign_phone_view, name='assign_phone'),
    path('assignments/', views.assignment_list_view, name='assignment_list'),
    path('assignments/<int:assignment_id>/approve/', views.approve_assignment_view, name='approve_assignment'),
    path('assignments/<int:assignment_id>/reject/', views.reject_assignment_view, name='reject_assignment'),
]
