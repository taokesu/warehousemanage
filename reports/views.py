from django.shortcuts import render
from django.db.models import F
from inventory.models import Stock, OutgoingItem
from inventory.utils import render_to_pdf
from django.http import HttpResponse

def low_stock_report(request):
    """
    Отчет по товарам, количество которых на складе ниже минимального порога.
    """
    # F() позволяет сравнивать два поля модели напрямую в базе данных
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

