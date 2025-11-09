from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('inventory-turnover/', views.inventory_turnover_report, name='inventory_turnover_report'),
]
