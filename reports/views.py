from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value, CharField
from django.db.models.functions import Concat
from inventory.models import Inventory, Transaction, Product
from django.views.generic import ListView, View
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import os
from django.conf import settings

def is_manager(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role.role_name == 'Менеджер'

@login_required
@user_passes_test(is_manager)
def report_list(request):
    return render(request, 'reports/report_list.html')

# ИСПРАВЛЕНО: Использует новую модель Inventory
@login_required
@user_passes_test(is_manager)
def stock_report(request):
    stocks = Inventory.objects.select_related('product', 'warehouse').order_by('warehouse__name', 'product__product_name')
    context = {
        'stocks': stocks
    }
    return render(request, 'reports/stock_report.html', context)

# ИСПРАВЛЕНО: Использует новую модель Inventory
@login_required
@user_passes_test(is_manager)
def low_stock_report(request):
    low_stocks = Inventory.objects.filter(quantity__lt=F('product__minimum_stock_level')).select_related('product', 'warehouse')
    context = {
        'low_stocks': low_stocks
    }
    return render(request, 'reports/low_stock_report.html', context)

# ИСПРАВЛЕНО: Логика отчета переписана под модель Transaction
@login_required
@user_passes_test(is_manager)
def sales_profitability_report(request):
    # Фильтруем только расходные транзакции
    sales_transactions = Transaction.objects.filter(document__document_type='Расход') \
        .values('product__product_name') \
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price')),
            # Для себестоимости нужна цена закупки, которой нет в расходной транзакции.
            # Это потребует более сложного запроса или денормализации данных.
            # Пока выведем отчет без себестоимости.
        ).order_by('-total_quantity')

    # Расчет общих показателей
    total_revenue = sales_transactions.aggregate(total=Sum('total_revenue'))['total'] or 0
    total_sales_count = sales_transactions.count()

    context = {
        'sales_data': sales_transactions,
        'total_revenue': total_revenue,
        'total_sales': total_sales_count,
        'gross_profit': 'N/A',
        'total_cogs': 'N/A', # Себестоимость пока не считаем
        'top_selling_products': sales_transactions[:5]
    }
    return render(request, 'reports/sales_profitability_report.html', context)


# ЗАГЛУШКА: Этот отчет требует сложной логики, временно отключен
@login_required
@user_passes_test(is_manager)
def inventory_turnover_report(request):
    context = {
        'turnover_ratio': 'N/A' # Расчет требует данных о закупках
    }
    return render(request, 'reports/inventory_turnover_report.html', context)
