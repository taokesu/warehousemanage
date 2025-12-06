from django.shortcuts import render
from django.db.models import F, Sum, Count, ExpressionWrapper, DecimalField
# from inventory.models import Stock, OutgoingItem, IncomingItem, Product
# from inventory.utils import render_to_pdf
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def report_list(request):
    """
    Отображает список всех доступных отчетов.
    """
    reports = [
        {
            'url': 'reports:low_stock_report',
            'title': 'Отчет по товарам, требующим закупки',
            'description': 'Показывает все товары на складе, количество которых меньше или равно минимальному порогу.'
        },
        {
            'url': 'reports:stock_report', 
            'title': 'Отчет по остаткам товаров',
            'description': 'Полная сводка по текущим остаткам всех товаров на всех складах.'
        },
        {
            'url': 'reports:sales_profitability_report',
            'title': 'Отчет по продажам и рентабельности',
            'description': 'Анализ продаж, прибыли и популярных товаров за период.'
        },
        {
            'url': 'reports:inventory_turnover_report',
            'title': 'Отчет по движению товаров',
            'description': 'Анализ поступлений и отгрузок товаров за период.'
        }
    ]
    context = {
        'report_title': 'Список отчетов',
        'reports': reports
    }
    return render(request, 'reports/report_list.html', context)

@login_required
def low_stock_report(request):
    context = {
        'items': [],
        'report_title': 'Отчет по товарам, требующим закупки'
    }
    return render(request, 'reports/low_stock_report.html', context)


@login_required
def stock_report(request):
    context = {
        'items': [],
        'report_title': 'Отчет по остаткам товаров',
        'total_stock_value': 0,
        'total_items': 0,
        'total_products': 0,
    }
    return render(request, 'reports/stock_report.html', context)

@login_required
def sales_profitability_report(request):
    context = {
        'report_title': 'Отчет по продажам и рентабельности',
        'total_revenue': 0,
        'total_cogs': 0,
        'gross_profit': 0,
        'total_sales': 0,
        'top_selling_products': [],
        'top_profitable_products': [],
    }
    return render(request, 'reports/sales_profitability_report.html', context)


@login_required
def inventory_turnover_report(request):
    context = {
        'incoming_items': [],
        'outgoing_items': [],
        'report_title': 'Отчет по движению товаров'
    }
    return render(request, 'reports/inventory_turnover_report.html', context)