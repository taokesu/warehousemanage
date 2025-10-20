from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('storekeeper/', views.storekeeper_dashboard_view, name='storekeeper_dashboard'),
    path('api/revenue-chart/', views.revenue_chart_data, name='revenue-chart-data'),
]
