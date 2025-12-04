from django.shortcuts import render
from django.db.models import F, Sum, Count, ExpressionWrapper, DecimalField
from inventory.models import Stock, OutgoingItem, IncomingItem, Product
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
                                 .values('product__product_name', 'product__serial_number', 'warehouse__name', 'quantity', 'product__minimum_stock_level')

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
    
    total_stock_value = 0
    for stock in stocks:
        total_stock_value += stock.quantity * stock.product.purchase_price

    total_items = Stock.objects.aggregate(total_items=Sum('quantity'))['total_items'] or 0
    
    context = {
        'items': stocks,
        'report_title': 'Отчет по остаткам товаров',
        'total_stock_value': total_stock_value,
        'total_items': total_items,
        'total_products': Product.objects.count(),
    }
    return render(request, 'reports/stock_report.html', context)

@login_required
def sales_profitability_report(request):
    """
    Отчет по продажам и рентабельности.
    """
    outgoing_items = OutgoingItem.objects.select_related('product')
    
    total_revenue = outgoing_items.aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    total_cogs = outgoing_items.aggregate(total=Sum(F('quantity') * F('product__purchase_price')))['total'] or 0
    gross_profit = total_revenue - total_cogs
    total_sales = outgoing_items.values('document').distinct().count()

    top_selling_products = OutgoingItem.objects.values('product__product_name') \
        .annotate(total_quantity=Sum('quantity')) \
        .order_by('-total_quantity')[:5]

    top_profitable_products = OutgoingItem.objects.select_related('product').annotate(
        profit=ExpressionWrapper((F('price') - F('product__purchase_price')) * F('quantity'), output_field=DecimalField())
    ).values('product__product_name').annotate(total_profit=Sum('profit')).order_by('-total_profit')[:5]

    context = {
        'report_title': 'Отчет по продажам и рентабельности',
        'total_revenue': total_revenue,
        'total_cogs': total_cogs,
        'gross_profit': gross_profit,
        'total_sales': total_sales,
        'top_selling_products': top_selling_products,
        'top_profitable_products': top_profitable_products,
    }
    return render(request, 'reports/sales_profitability_report.html', context)


@login_required
def inventory_turnover_report(request):
    """
    Отчет по движению товаров за период.
    """
    incoming = IncomingItem.objects.values('product__product_name', 'product__serial_number').annotate(total_incoming=Sum('quantity')).order_by()
    outgoing = OutgoingItem.objects.values('product__product_name', 'product__serial_number').annotate(total_outgoing=Sum('quantity')).order_by()
    
    turnover_data = {}
    for item in incoming:
        product_name = item['product__product_name']
        if product_name not in turnover_data:
            turnover_data[product_name] = {'incoming': 0, 'outgoing': 0, 'serial_number': item['product__serial_number']}
        turnover_data[product_name]['incoming'] += item['total_incoming']

    for item in outgoing:
        product_name = item['product__product_name']
        if product_name not in turnover_data:
            turnover_data[product_name] = {'incoming': 0, 'outgoing': 0, 'serial_number': item['product__serial_number']}
        turnover_data[product_name]['outgoing'] += item['total_outgoing']

    context = {
        'turnover_data': turnover_data,
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