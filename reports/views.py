from django.shortcuts import render
from inventory.models import Stock, OutgoingItem, Product
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib.auth.decorators import user_passes_test, login_required
from datetime import datetime, time

def is_manager(user):
    return user.is_authenticated and user.role and user.role.role_name == 'Менеджер'

@login_required
@user_passes_test(is_manager)
def report_list(request):
    reports = [
        {'title': 'Отчет по остаткам товаров', 'url_name': 'stock_report'},
        {'title': 'Отчет по продажам и рентабельности', 'url_name': 'sales_profitability_report'},
        {'title': 'Отчет по товарам к закупке', 'url_name': 'low_stock_report'},
    ]
    return render(request, 'reports/report_list.html', {'reports': reports})

@login_required
@user_passes_test(is_manager)
def stock_report(request):
    stock_details = Stock.objects.select_related('product', 'warehouse').annotate(
        product_name=F('product__product_name'),
        warehouse_name=F('warehouse__name'),
        total_cost_price=ExpressionWrapper(F('quantity') * F('product__purchase_price'), output_field=DecimalField()),
        avg_cost_price=F('product__purchase_price'),
        total_sale_price=ExpressionWrapper(F('quantity') * F('product__selling_price'), output_field=DecimalField()),
        product_sale_price=F('product__selling_price')
    ).order_by('product__product_name', 'warehouse__name')

    total_asset_value = stock_details.aggregate(grand_total=Sum('total_cost_price'))['grand_total'] or 0

    context = {
        'stock_details': stock_details,
        'total_asset_value': total_asset_value,
    }
    return render(request, 'reports/stock_report.html', context)

@login_required
@user_passes_test(is_manager)
def sales_profitability_report(request):
    sales_items_query = OutgoingItem.objects.filter(product__selling_price__gt=0).select_related(
        'product', 'outgoing_transaction__document'
    )

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        sales_items_query = sales_items_query.filter(outgoing_transaction__document__document_date__gte=start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date_with_time = datetime.combine(end_date, time.max)
        sales_items_query = sales_items_query.filter(outgoing_transaction__document__document_date__lte=end_date_with_time)

    sales_items = sales_items_query.annotate(
        cost_price=F('product__purchase_price'),
        sale_price=F('product__selling_price'),
        profit=ExpressionWrapper(
            (F('product__selling_price') - F('product__purchase_price')) * F('quantity'),
            output_field=DecimalField()
        )
    ).order_by('-outgoing_transaction__document__document_date')

    totals = sales_items.aggregate(
        total_revenue=Sum(F('product__selling_price') * F('quantity'), output_field=DecimalField()),
        total_cost=Sum(F('product__purchase_price') * F('quantity'), output_field=DecimalField()),
        total_profit=Sum('profit')
    )

    context = {
        'sales_items': sales_items,
        'total_revenue': totals.get('total_revenue') or 0,
        'total_cost': totals.get('total_cost') or 0,
        'total_profit': totals.get('total_profit') or 0,
    }
    return render(request, 'reports/sales_profitability_report.html', context)

@login_required
@user_passes_test(is_manager)
def low_stock_report(request):
    low_stock_products = Stock.objects.filter(
        quantity__lte=F('product__minimum_stock_level')
    ).select_related('product', 'warehouse').order_by('product__product_name', 'warehouse__name')

    context = {
        'low_stock_products': low_stock_products,
    }
    return render(request, 'reports/low_stock_report.html', context)
