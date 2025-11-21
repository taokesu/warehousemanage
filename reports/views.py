from django.shortcuts import render
from django.db.models import F, Sum, Count
from inventory.models import Stock, OutgoingItem, IncomingItem
from inventory.utils import render_to_pdf
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
    """
    Отчет по товарам, количество которых на складе ниже минимального порога.
    """
    low_stock_items = Stock.objects.filter(quantity__lte=F('product__minimum_stock_level')) \
                                 .select_related('product', 'warehouse') \
                                 .values('product__product_name', 'product__sku', 'warehouse__name', 'quantity', 'product__minimum_stock_level')

    context = {
        'items': low_stock_items,
        'report_title': 'Отчет по товарам, требующим закупки'
    }

    if 'pdf' in request.GET:
        pdf = render_to_pdf('reports/pdf/low_stock_report_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "low_stock_report.pdf"
            content = f"attachment; filename='{filename}'"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Ошибка генерации PDF", status=500)

    return render(request, 'reports/low_stock_report.html', context)


@login_required
def stock_report(request):
    """
    Отчет по текущим остаткам товаров на всех складах.
    """
    stocks = Stock.objects.select_related('product', 'warehouse').order_by('product__product_name')
    context = {
        'items': stocks,
        'report_title': 'Отчет по остаткам товаров'
    }
    return render(request, 'reports/stock_report.html', context)

@login_required
def sales_profitability_report(request):
    """
    Отчет по продажам и рентабельности (заглушка).
    """
    context = {
        'report_title': 'Отчет по продажам и рентабельности'
    }
    return render(request, 'reports/sales_profitability_report.html', context)


@login_required
def inventory_turnover_report(request):
    """
    Отчет по движению товаров за период.
    """
    incoming = IncomingItem.objects.values('product__product_name').annotate(total_incoming=Sum('quantity')).order_by()
    outgoing = OutgoingItem.objects.values('product__product_name').annotate(total_outgoing=Sum('quantity')).order_by()

    context = {
        'incoming_items': incoming,
        'outgoing_items': outgoing,
        'report_title': 'Отчет по движению товаров'
    }
    
    if 'pdf' in request.GET:
        pdf = render_to_pdf('reports/pdf/inventory_turnover_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "inventory_turnover_report.pdf"
            content = f"attachment; filename='{filename}'"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Ошибка генерации PDF", status=500)

    return render(request, 'reports/inventory_turnover_report.html', context)