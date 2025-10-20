from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('incoming/', views.incoming_transaction_view, name='incoming_transaction'),
    path('outgoing/', views.outgoing_transaction_view, name='outgoing_transaction'),
    path('documents/', views.document_list, name='document_list'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('incoming/create/', views.incoming_transaction_view, name='incoming_transaction_create'),
    path('outgoing/create/', views.outgoing_transaction_view, name='outgoing_transaction_create'),
]
