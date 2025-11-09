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
    context = {
        'report_title': 'Список отчетов'
    }
    return render(request, 'reports/report_list.html', context)

@login_required
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
        pdf = render_to_pdf('reports/pdf/report_template.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "low_stock_report.pdf"
            content = f"attachment; filename='{filename}'"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Ошибка генерации PDF", status=500)

    return render(request, 'reports/low_stock_report.html', context)

@login_required
def inventory_turnover_report(request):
    """
    Отчет по движению товаров за период.
    """
    # Для простоты пока берем все движения
    incoming = IncomingItem.objects.values('product__name').annotate(total_incoming=Sum('quantity')).order_by()
    outgoing = OutgoingItem.objects.values('product__name').annotate(total_outgoing=Sum('quantity')).order_by()

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
