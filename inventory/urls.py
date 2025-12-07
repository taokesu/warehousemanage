
from django.urls import path
from .views import (
    stock_list, document_list, document_detail, 
    incoming_form_view, outgoing_form_view, StorekeeperDashboardView, document_pdf_view
)

urlpatterns = [
    path('stock/', stock_list, name='stock_list'),
    path('documents/', document_list, name='document_list'),
    path('documents/<int:pk>/', document_detail, name='document_detail'),
    path('documents/create/incoming/', incoming_form_view, name='incoming_transaction_create'),
    path('documents/create/outgoing/', outgoing_form_view, name='outgoing_transaction_create'),
    path('storekeeper/dashboard/', StorekeeperDashboardView.as_view(), name='storekeeper_dashboard'),
    path('documents/<int:document_id>/pdf/', document_pdf_view, name='document_pdf'),
]
