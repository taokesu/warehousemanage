from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('stock/', views.stock_report, name='stock_report'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('sales/', views.sales_profitability_report, name='sales_profitability_report'),
    path('turnover/', views.inventory_turnover_report, name='inventory_turnover_report'),
]
