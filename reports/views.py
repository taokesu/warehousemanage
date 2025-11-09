from django.shortcuts import render
from django.db.models import F, Sum, Count
from inventory.models import Stock, OutgoingItem, IncomingItem
from inventory.utils import render_to_pdf
from django.http import HttpResponse

def low_stock_report(request):
    """
    Отчет по товарам, количество которых на складе ниже минимального порога.
    """
    low_stock_items = Stock.objects.filter(quantity__lte=F('product__minimum_stock_level')).select_related('product', 'warehouse')
    
    context = {
        'items': low_stock_items,
        'report_title': 'Отчет по товарам, требующим закупки'
    }

    if 'pdf' in request.GET:
        pdf = render_to_pdf('reports/pdf/low_stock_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "low_stock_report.pdf"
            content = f"attachment; filename='{filename}'"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Ошибка генерации PDF", status=500)

    return render(request, 'reports/low_stock_report.html', context)

def inventory_turnover_report(request):
    """
    Отчет по движению товаров за период.
    """
    # Для простоты пока берем все движения
    incoming = IncomingItem.objects.values('product__name').annotate(total_incoming=Sum('quantity')).order_by()
    outgoing = OutgoingItem.objects.values('product__name').annotate(total_outgoing=Sum('quantity')).order_by()

    # Это упрощенный пример. В реальности нужно будет объединять эти данные
    # и учитывать начальные и конечные остатки для расчета оборачиваемости.
    
    # TODO: Реализовать более сложную логику для объединения и расчета.

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
