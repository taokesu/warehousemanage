
from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('stock/', views.stock_report, name='stock_report'),
    path('restock/', views.restock_needed_report, name='restock_needed_report'),
    path('sales/', views.sales_report, name='sales_report'),
    path('turnover/', views.product_turnover_report, name='product_turnover_report'),
]
