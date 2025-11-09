from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('inventory-turnover/', views.inventory_turnover_report, name='inventory_turnover_report'),
    # Восстановленные маршруты
    path('stock/', views.stock_report, name='stock_report'),
    path('sales-profitability/', views.sales_profitability_report, name='sales_profitability_report'),
]
