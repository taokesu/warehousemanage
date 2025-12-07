from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from inventory.models import Stock, IncomingItem, OutgoingItem, Product
from django.views.generic import ListView
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

@login_required
@user_passes_test(is_manager)
def stock_report(request):
    stocks = Stock.objects.select_related('product', 'warehouse').order_by('warehouse__name', 'product__name')
    context = {
        'stocks': stocks
    }
    return render(request, 'reports/stock_report.html', context)

@login_required
@user_passes_test(is_manager)
def low_stock_report(request):
    low_stocks = Stock.objects.filter(quantity__lt=F('product__minimum_stock_level')).select_related('product', 'warehouse')
    context = {
        'low_stocks': low_stocks
    }
    return render(request, 'reports/low_stock_report.html', context)

@login_required
@user_passes_test(is_manager)
def inventory_turnover_report(request):
    # Эта логика может быть сложной и требует более детального анализа данных
    # Ниже представлен упрощенный пример
    total_cost_of_goods_sold = OutgoingItem.objects.aggregate(
        total_cogs=Sum(F('quantity') * F('item__purchase_price'))
    )['total_cogs'] or 0
    
    average_inventory_cost = (Stock.objects.aggregate(
        avg_inv=Sum(F('quantity') * F('product__purchase_price'))
    )['avg_inv'] or 0) / 2 # Упрощенный расчет среднего запаса

    turnover_ratio = total_cost_of_goods_sold / average_inventory_cost if average_inventory_cost else 0

    context = {
        'turnover_ratio': turnover_ratio
    }
    return render(request, 'reports/inventory_turnover_report.html', context)

@login_required
@user_passes_test(is_manager)
def sales_profitability_report(request):
    sales = OutgoingItem.objects.annotate(
        profit=ExpressionWrapper(
            F('item__selling_price') - F('item__purchase_price'),
            output_field=DecimalField()
        )
    ).select_related('item__product')

    context = {
        'sales': sales
    }
    return render(request, 'reports/sales_profitability_report.html', context)


class ReportPDFView(View):
    template_name = None
    pdf_filename = 'report.pdf'

    def get_context_data(self, **kwargs):
        return {}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        template = get_template(self.template_name)
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.pdf_filename}"'

        # Путь к шрифту
        font_path = os.path.join(settings.STATICFILES_DIRS[0], 'fonts', 'LiberationSans-Regular.ttf')

        pisa_status = pisa.CreatePDF(
            html, dest=response, 
            link_callback=lambda uri, rel: os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, "")), 
            encoding='UTF-8', 
            default_font='LiberationSans',
            font_config=pisa.pisaFontData(font_path)
        )

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

class StockReportPDF(ReportPDFView):
    template_name = 'reports/pdf/stock_report_pdf.html'
    pdf_filename = 'stock_report.pdf'

    def get_context_data(self, **kwargs):
        return {'stocks': Stock.objects.select_related('product', 'warehouse').all()}

class LowStockReportPDF(ReportPDFView):
    template_name = 'reports/pdf/low_stock_report_pdf.html'
    pdf_filename = 'low_stock_report.pdf'

    def get_context_data(self, **kwargs):
        return {'low_stocks': Stock.objects.filter(quantity__lt=10).select_related('product', 'warehouse')}

class InventoryTurnoverReportPDF(ReportPDFView):
    template_name = 'reports/pdf/inventory_turnover_report_pdf.html'
    pdf_filename = 'inventory_turnover_report.pdf'

    def get_context_data(self, **kwargs):
        # Упрощенная логика, как и в веб-версии
        total_cogs = OutgoingItem.objects.aggregate(total_cogs=Sum(F('quantity') * F('item__purchase_price'))).get('total_cogs', 0) or 0
        avg_inv_cost = (Stock.objects.aggregate(avg_inv=Sum(F('quantity') * F('product__purchase_price'))).get('avg_inv', 0) or 0) / 2
        turnover_ratio = total_cogs / avg_inv_cost if avg_inv_cost else 0
        return {'turnover_ratio': turnover_ratio}

class SalesProfitabilityReportPDF(ReportPDFView):
    template_name = 'reports/pdf/sales_profitability_report_pdf.html'
    pdf_filename = 'sales_profitability_report.pdf'

    def get_context_data(self, **kwargs):
        sales = OutgoingItem.objects.annotate(
            profit=ExpressionWrapper(F('item__selling_price') - F('item__purchase_price'), output_field=DecimalField())
        ).select_related('item__product')
        return {'sales': sales}
