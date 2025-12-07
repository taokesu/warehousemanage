from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('stock/', views.stock_report, name='stock_report'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('inventory-turnover/', views.inventory_turnover_report, name='inventory_turnover_report'),
    path('sales-profitability/', views.sales_profitability_report, name='sales_profitability_report'),

    # PDF reports (временно отключены для исправления запуска сервера)
    # path('stock/pdf/', views.StockReportPDF.as_view(), name='stock_report_pdf'),
    # path('low-stock/pdf/', views.LowStockReportPDF.as_view(), name='low_stock_report_pdf'),
    # path('inventory-turnover/pdf/', views.InventoryTurnoverReportPDF.as_view(), name='inventory_turnover_report_pdf'),
    # path('sales-profitability/pdf/', views.SalesProfitabilityReportPDF.as_view(), name='sales_profitability_report_pdf'),
]
